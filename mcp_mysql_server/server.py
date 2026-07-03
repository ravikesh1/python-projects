"""MCP server exposing MySQL databases over stdio.

Tools:
  - list_databases
  - list_tables
  - describe_table
  - read_query    (SELECT / SHOW / DESCRIBE / EXPLAIN only)
  - write_query   (INSERT / UPDATE / DELETE; enabled only when MYSQL_ALLOW_WRITE=true)
  - execute_ddl   (CREATE / ALTER / DROP / TRUNCATE; enabled only when MYSQL_ALLOW_DDL=true)

Resources:
  - mysql://<database>/<table>/schema  -> CREATE TABLE statement
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pymysql
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, TextContent, Tool

logger = logging.getLogger("mcp-mysql-server")

READ_ONLY_PREFIXES = ("select", "show", "describe", "desc", "explain", "with")
WRITE_PREFIXES = ("insert", "update", "delete", "replace")
DDL_PREFIXES = ("create", "alter", "drop", "truncate", "rename")

# Single source of truth for each tool's declared arguments, shared by
# list_tools() (advertised schema) and _extra_keys() (anomaly detection).
TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "list_databases": {"type": "object", "properties": {}},
    "list_tables": {
        "type": "object",
        "properties": {
            "database": {
                "type": "string",
                "description": "Database name. Optional if MYSQL_DATABASE is set.",
            },
        },
    },
    "describe_table": {
        "type": "object",
        "properties": {
            "table": {"type": "string", "description": "Table name."},
            "database": {
                "type": "string",
                "description": "Database name. Optional if MYSQL_DATABASE is set.",
            },
        },
        "required": ["table"],
    },
    "read_query": {
        "type": "object",
        "properties": {"sql": {"type": "string", "description": "Read-only SQL statement."}},
        "required": ["sql"],
    },
    "write_query": {
        "type": "object",
        "properties": {"sql": {"type": "string", "description": "DML SQL statement."}},
        "required": ["sql"],
    },
    "execute_ddl": {
        "type": "object",
        "properties": {"sql": {"type": "string", "description": "DDL SQL statement."}},
        "required": ["sql"],
    },
}


def _extra_keys(name: str, args: dict[str, Any]) -> list[str]:
    """Argument keys present in ``args`` but not declared in the tool's schema.

    Returns [] for unknown tool names -- _dispatch already raises its own
    "Unknown tool" ValueError for those.
    """
    schema = TOOL_SCHEMAS.get(name)
    if schema is None:
        return []
    allowed = set(schema.get("properties", {}))
    return sorted(set(args) - allowed)


@dataclass(frozen=True)
class Config:
    host: str
    port: int
    user: str
    password: str
    database: str | None
    charset: str
    allow_write: bool
    allow_ddl: bool
    row_limit: int
    audit_log: bool
    audit_log_path: str

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            host=os.getenv("MYSQL_HOST", "127.0.0.1"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE") or None,
            charset=os.getenv("MYSQL_CHARSET", "utf8mb4"),
            allow_write=_envbool("MYSQL_ALLOW_WRITE", False),
            allow_ddl=_envbool("MYSQL_ALLOW_DDL", False),
            row_limit=int(os.getenv("MYSQL_ROW_LIMIT", "1000")),
            audit_log=_envbool("MYSQL_AUDIT_LOG", False),
            audit_log_path=os.getenv("MYSQL_AUDIT_LOG_PATH", "logs/mcp-mysql-audit.jsonl"),
        )


def _envbool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _connect(cfg: Config) -> pymysql.connections.Connection:
    return pymysql.connect(
        host=cfg.host,
        port=cfg.port,
        user=cfg.user,
        password=cfg.password,
        database=cfg.database,
        charset=cfg.charset,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def _classify(sql: str) -> str:
    stripped = sql.lstrip().lower()
    stripped = re.sub(r"^/\*.*?\*/\s*", "", stripped, flags=re.DOTALL)
    stripped = re.sub(r"^--[^\n]*\n", "", stripped)
    first = stripped.split(None, 1)[0] if stripped else ""
    if first in READ_ONLY_PREFIXES:
        return "read"
    if first in WRITE_PREFIXES:
        return "write"
    if first in DDL_PREFIXES:
        return "ddl"
    return "other"


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, timedelta):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value.hex()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _format_rows(rows: list[dict[str, Any]], row_limit: int) -> str:
    truncated = len(rows) > row_limit
    if truncated:
        rows = rows[:row_limit]
    payload = {
        "row_count": len(rows),
        "truncated": truncated,
        "rows": rows,
    }
    return json.dumps(payload, default=_json_default, indent=2)


AUDIT_TRUNCATE_LEN = 500  # cap individual string field length in audit records


def _audit_truncate(value: Any, limit: int = AUDIT_TRUNCATE_LEN) -> Any:
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + f"...(truncated, {len(value)} chars)"
    if isinstance(value, dict):
        return {k: _audit_truncate(v, limit) for k, v in value.items()}
    if isinstance(value, list):
        return [_audit_truncate(v, limit) for v in value]
    return value


def _write_audit_record(
    cfg: Config,
    *,
    name: str,
    args: dict[str, Any],
    outcome: str,
    extra_keys: list[str],
) -> None:
    """Append one JSONL audit record. Must never raise -- a logging failure
    must never break a real tool call."""
    if not cfg.audit_log:
        return
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": name,
        "arguments": _audit_truncate(args),
        "outcome": outcome,
        "anomalous": bool(extra_keys),
        "extra_keys": extra_keys,
    }
    try:
        path = Path(cfg.audit_log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, default=_json_default, ensure_ascii=False) + "\n")
    except OSError:
        logger.warning("Failed to write audit log entry for tool %s", name, exc_info=True)


def build_server(cfg: Config) -> Server:
    server: Server = Server("mcp-mysql-server")

    def run_query(sql: str, params: tuple | None = None) -> list[dict[str, Any]]:
        conn = _connect(cfg)
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                if cur.description is None:
                    return [{"affected_rows": cur.rowcount}]
                return list(cur.fetchall())
        finally:
            conn.close()

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        if not cfg.database:
            return []
        tables = run_query("SHOW TABLES")
        resources: list[Resource] = []
        for row in tables:
            table = next(iter(row.values()))
            resources.append(
                Resource(
                    uri=f"mysql://{cfg.database}/{table}/schema",
                    name=f"{cfg.database}.{table} schema",
                    mimeType="text/plain",
                    description=f"CREATE TABLE statement for {table}",
                )
            )
        return resources

    @server.read_resource()
    async def read_resource(uri: str) -> str:
        match = re.match(r"^mysql://([^/]+)/([^/]+)/schema$", str(uri))
        if not match:
            raise ValueError(f"Unsupported resource URI: {uri}")
        db, table = match.group(1), match.group(2)
        rows = run_query(f"SHOW CREATE TABLE `{db}`.`{table}`")
        if not rows:
            raise ValueError(f"No schema found for {db}.{table}")
        create_stmt = rows[0].get("Create Table") or rows[0].get("Create View")
        return create_stmt or json.dumps(rows[0], default=_json_default)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        tools = [
            Tool(
                name="list_databases",
                description="List all databases visible to the configured MySQL user.",
                inputSchema=TOOL_SCHEMAS["list_databases"],
            ),
            Tool(
                name="list_tables",
                description="List tables in a database. Uses the configured database if 'database' is omitted.",
                inputSchema=TOOL_SCHEMAS["list_tables"],
            ),
            Tool(
                name="describe_table",
                description="Return column definitions for a table.",
                inputSchema=TOOL_SCHEMAS["describe_table"],
            ),
            Tool(
                name="read_query",
                description=(
                    "Execute a read-only SQL query (SELECT / SHOW / DESCRIBE / EXPLAIN / WITH). "
                    f"Results are capped at {cfg.row_limit} rows."
                ),
                inputSchema=TOOL_SCHEMAS["read_query"],
            ),
        ]
        if cfg.allow_write:
            tools.append(
                Tool(
                    name="write_query",
                    description="Execute an INSERT / UPDATE / DELETE / REPLACE statement. Returns affected row count.",
                    inputSchema=TOOL_SCHEMAS["write_query"],
                )
            )
        if cfg.allow_ddl:
            tools.append(
                Tool(
                    name="execute_ddl",
                    description="Execute a DDL statement (CREATE / ALTER / DROP / TRUNCATE / RENAME).",
                    inputSchema=TOOL_SCHEMAS["execute_ddl"],
                )
            )
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        args = arguments or {}
        extra_keys = _extra_keys(name, args)
        if extra_keys:
            logger.warning("Tool %s called with unexpected argument(s): %s", name, extra_keys)

        outcome = "success"
        try:
            text = _dispatch(name, args)
        except PermissionError as exc:
            outcome, text = "permission_denied", f"Permission denied: {exc}"
        except ValueError as exc:
            outcome, text = "invalid_request", f"Invalid request: {exc}"
        except pymysql.MySQLError as exc:
            outcome, text = "mysql_error", f"MySQL error: {exc}"
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected error handling tool %s", name)
            outcome, text = "unexpected_error", f"Unexpected error: {exc}"

        _write_audit_record(cfg, name=name, args=args, outcome=outcome, extra_keys=extra_keys)
        return [TextContent(type="text", text=text)]

    def _dispatch(name: str, args: dict[str, Any]) -> str:
        if name == "list_databases":
            rows = run_query("SHOW DATABASES")
            return _format_rows(rows, cfg.row_limit)

        if name == "list_tables":
            db = args.get("database") or cfg.database
            if not db:
                raise ValueError("No database provided and MYSQL_DATABASE is not set.")
            rows = run_query(
                "SELECT table_name, table_type, engine, table_rows "
                "FROM information_schema.tables WHERE table_schema = %s",
                (db,),
            )
            return _format_rows(rows, cfg.row_limit)

        if name == "describe_table":
            table = args.get("table")
            if not table:
                raise ValueError("'table' is required.")
            db = args.get("database") or cfg.database
            if not db:
                raise ValueError("No database provided and MYSQL_DATABASE is not set.")
            rows = run_query(
                "SELECT column_name, column_type, is_nullable, column_key, column_default, extra "
                "FROM information_schema.columns "
                "WHERE table_schema = %s AND table_name = %s "
                "ORDER BY ordinal_position",
                (db, table),
            )
            return _format_rows(rows, cfg.row_limit)

        if name == "read_query":
            sql = args.get("sql", "")
            kind = _classify(sql)
            if kind != "read":
                raise PermissionError(
                    "read_query only accepts SELECT / SHOW / DESCRIBE / EXPLAIN / WITH statements."
                )
            rows = run_query(sql)
            return _format_rows(rows, cfg.row_limit)

        if name == "write_query":
            if not cfg.allow_write:
                raise PermissionError("Writes are disabled. Set MYSQL_ALLOW_WRITE=true to enable.")
            sql = args.get("sql", "")
            if _classify(sql) != "write":
                raise PermissionError("write_query only accepts INSERT / UPDATE / DELETE / REPLACE.")
            rows = run_query(sql)
            return _format_rows(rows, cfg.row_limit)

        if name == "execute_ddl":
            if not cfg.allow_ddl:
                raise PermissionError("DDL is disabled. Set MYSQL_ALLOW_DDL=true to enable.")
            sql = args.get("sql", "")
            if _classify(sql) != "ddl":
                raise PermissionError(
                    "execute_ddl only accepts CREATE / ALTER / DROP / TRUNCATE / RENAME."
                )
            rows = run_query(sql)
            return _format_rows(rows, cfg.row_limit)

        raise ValueError(f"Unknown tool: {name}")

    return server


async def _run() -> None:
    load_dotenv()
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    cfg = Config.from_env()
    server = build_server(cfg)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
