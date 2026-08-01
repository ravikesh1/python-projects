"""MCP server for multi-database schema introspection.

Tools:
  - list_datasources      List configured datasources
  - list_tables            List tables in a datasource
  - describe_table         Column definitions for a table
  - get_create_statement   DDL for a table
  - list_foreign_keys      Foreign key relationships
  - list_indexes           Indexes on a table
  - search_columns         Search columns by name pattern
  - get_erd                Entity-relationship data (tables + columns + FKs)

Resources:
  - schema://<datasource>/<table>  CREATE TABLE statement
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import pymysql
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, TextContent, Tool

logger = logging.getLogger("mcp-db-schemas")


@dataclass(frozen=True)
class DatasourceConfig:
    name: str
    type: str
    host: str = "127.0.0.1"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str = ""
    charset: str = "utf8mb4"
    path: str = ""

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DatasourceConfig:
        return cls(
            name=d["name"],
            type=d["type"],
            host=d.get("host", "127.0.0.1"),
            port=int(d.get("port", 3306)),
            user=d.get("user", "root"),
            password=d.get("password", ""),
            database=d.get("database", ""),
            charset=d.get("charset", "utf8mb4"),
            path=d.get("path", ""),
        )


class Backend(ABC):
    @abstractmethod
    def list_tables(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    def describe_table(self, table: str) -> list[dict[str, Any]]: ...

    @abstractmethod
    def get_create_statement(self, table: str) -> str: ...

    @abstractmethod
    def list_foreign_keys(self, table: str | None = None) -> list[dict[str, Any]]: ...

    @abstractmethod
    def list_indexes(self, table: str) -> list[dict[str, Any]]: ...


class MySQLBackend(Backend):
    def __init__(self, cfg: DatasourceConfig):
        self._cfg = cfg

    def _connect(self) -> pymysql.connections.Connection:
        return pymysql.connect(
            host=self._cfg.host,
            port=self._cfg.port,
            user=self._cfg.user,
            password=self._cfg.password,
            database=self._cfg.database,
            charset=self._cfg.charset,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )

    def _query(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return list(cur.fetchall())
        finally:
            conn.close()

    def list_tables(self) -> list[dict[str, Any]]:
        return self._query(
            "SELECT table_name, table_type, engine, table_rows, table_comment "
            "FROM information_schema.tables WHERE table_schema = %s "
            "ORDER BY table_name",
            (self._cfg.database,),
        )

    def describe_table(self, table: str) -> list[dict[str, Any]]:
        return self._query(
            "SELECT column_name, column_type, is_nullable, column_key, "
            "column_default, extra, column_comment "
            "FROM information_schema.columns "
            "WHERE table_schema = %s AND table_name = %s "
            "ORDER BY ordinal_position",
            (self._cfg.database, table),
        )

    def get_create_statement(self, table: str) -> str:
        rows = self._query(f"SHOW CREATE TABLE `{self._cfg.database}`.`{table}`")
        if not rows:
            raise ValueError(f"Table not found: {table}")
        return rows[0].get("Create Table") or rows[0].get("Create View") or ""

    def list_foreign_keys(self, table: str | None = None) -> list[dict[str, Any]]:
        sql = (
            "SELECT constraint_name, table_name, column_name, "
            "referenced_table_name, referenced_column_name "
            "FROM information_schema.key_column_usage "
            "WHERE table_schema = %s AND referenced_table_name IS NOT NULL"
        )
        params: tuple = (self._cfg.database,)
        if table:
            sql += " AND table_name = %s"
            params = (self._cfg.database, table)
        sql += " ORDER BY table_name, constraint_name, ordinal_position"
        return self._query(sql, params)

    def list_indexes(self, table: str) -> list[dict[str, Any]]:
        return self._query(
            "SELECT index_name, column_name, non_unique, seq_in_index, index_type "
            "FROM information_schema.statistics "
            "WHERE table_schema = %s AND table_name = %s "
            "ORDER BY index_name, seq_in_index",
            (self._cfg.database, table),
        )


class SQLiteBackend(Backend):
    def __init__(self, cfg: DatasourceConfig):
        self._path = cfg.path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def _query(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        conn = self._connect()
        try:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def list_tables(self) -> list[dict[str, Any]]:
        return self._query(
            "SELECT name AS table_name, type AS table_type "
            "FROM sqlite_master WHERE type IN ('table', 'view') "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )

    def describe_table(self, table: str) -> list[dict[str, Any]]:
        rows = self._query(f"PRAGMA table_info(`{table}`)")
        return [
            {
                "column_name": r["name"],
                "column_type": r["type"],
                "is_nullable": "YES" if not r["notnull"] else "NO",
                "column_key": "PRI" if r["pk"] else "",
                "column_default": r["dflt_value"],
            }
            for r in rows
        ]

    def get_create_statement(self, table: str) -> str:
        rows = self._query(
            "SELECT sql FROM sqlite_master WHERE type IN ('table','view') AND name = ?",
            (table,),
        )
        if not rows:
            raise ValueError(f"Table not found: {table}")
        return rows[0]["sql"] or ""

    def list_foreign_keys(self, table: str | None = None) -> list[dict[str, Any]]:
        if table:
            rows = self._query(f"PRAGMA foreign_key_list(`{table}`)")
            return [
                {
                    "table_name": table,
                    "column_name": r["from"],
                    "referenced_table_name": r["table"],
                    "referenced_column_name": r["to"],
                }
                for r in rows
            ]
        result: list[dict[str, Any]] = []
        for t in self.list_tables():
            result.extend(self.list_foreign_keys(t["table_name"]))
        return result

    def list_indexes(self, table: str) -> list[dict[str, Any]]:
        indexes = self._query(f"PRAGMA index_list(`{table}`)")
        result: list[dict[str, Any]] = []
        for idx in indexes:
            cols = self._query(f"PRAGMA index_info(`{idx['name']}`)")
            for col in cols:
                result.append({
                    "index_name": idx["name"],
                    "column_name": col["name"],
                    "non_unique": 1 if not idx["unique"] else 0,
                    "seq_in_index": col["seqno"] + 1,
                })
        return result


def _make_backend(cfg: DatasourceConfig) -> Backend:
    if cfg.type == "mysql":
        return MySQLBackend(cfg)
    if cfg.type == "sqlite":
        return SQLiteBackend(cfg)
    raise ValueError(f"Unsupported datasource type: {cfg.type}")


def load_datasources() -> dict[str, tuple[DatasourceConfig, Backend]]:
    raw = os.getenv("DATASOURCES", "[]")
    configs: list[dict[str, Any]] = json.loads(raw)
    result: dict[str, tuple[DatasourceConfig, Backend]] = {}
    for item in configs:
        cfg = DatasourceConfig.from_dict(item)
        result[cfg.name] = (cfg, _make_backend(cfg))
    return result


def build_server(datasources: dict[str, tuple[DatasourceConfig, Backend]]) -> Server:
    server: Server = Server("mcp-db-schemas")

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        resources: list[Resource] = []
        for ds_name, (cfg, backend) in datasources.items():
            try:
                tables = backend.list_tables()
            except Exception:
                logger.warning("Failed to list tables for %s", ds_name)
                continue
            for row in tables:
                table = row["table_name"]
                resources.append(
                    Resource(
                        uri=f"schema://{ds_name}/{table}",
                        name=f"{ds_name}.{table}",
                        mimeType="text/plain",
                        description=f"Schema for {ds_name}.{table} ({cfg.type})",
                    )
                )
        return resources

    @server.read_resource()
    async def read_resource(uri: str) -> str:
        match = re.match(r"^schema://([^/]+)/([^/]+)$", str(uri))
        if not match:
            raise ValueError(f"Unsupported resource URI: {uri}")
        ds_name, table = match.group(1), match.group(2)
        if ds_name not in datasources:
            raise ValueError(f"Unknown datasource: {ds_name}")
        _, backend = datasources[ds_name]
        return backend.get_create_statement(table)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="list_datasources",
                description="List all configured database datasources with their type and connection info.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="list_tables",
                description="List all tables in a datasource.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "datasource": {"type": "string", "description": "Datasource name."},
                    },
                    "required": ["datasource"],
                },
            ),
            Tool(
                name="describe_table",
                description="Get column definitions (name, type, nullable, key, default) for a table.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "datasource": {"type": "string", "description": "Datasource name."},
                        "table": {"type": "string", "description": "Table name."},
                    },
                    "required": ["datasource", "table"],
                },
            ),
            Tool(
                name="get_create_statement",
                description="Get the CREATE TABLE DDL statement for a table.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "datasource": {"type": "string", "description": "Datasource name."},
                        "table": {"type": "string", "description": "Table name."},
                    },
                    "required": ["datasource", "table"],
                },
            ),
            Tool(
                name="list_foreign_keys",
                description="List foreign key relationships. Optionally filter by table name.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "datasource": {"type": "string", "description": "Datasource name."},
                        "table": {"type": "string", "description": "Table name to filter by (optional)."},
                    },
                    "required": ["datasource"],
                },
            ),
            Tool(
                name="list_indexes",
                description="List indexes on a table.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "datasource": {"type": "string", "description": "Datasource name."},
                        "table": {"type": "string", "description": "Table name."},
                    },
                    "required": ["datasource", "table"],
                },
            ),
            Tool(
                name="search_columns",
                description="Search for columns matching a name pattern across all tables in a datasource.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "datasource": {"type": "string", "description": "Datasource name."},
                        "pattern": {
                            "type": "string",
                            "description": "Column name substring to search for (case-insensitive).",
                        },
                    },
                    "required": ["datasource", "pattern"],
                },
            ),
            Tool(
                name="get_erd",
                description=(
                    "Get entity-relationship data for a datasource: "
                    "all tables with their columns and foreign key relationships."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "datasource": {"type": "string", "description": "Datasource name."},
                    },
                    "required": ["datasource"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        try:
            text = _dispatch(name, arguments or {})
        except ValueError as exc:
            text = f"Invalid request: {exc}"
        except pymysql.MySQLError as exc:
            text = f"MySQL error: {exc}"
        except sqlite3.Error as exc:
            text = f"SQLite error: {exc}"
        except Exception as exc:
            logger.exception("Unexpected error handling tool %s", name)
            text = f"Unexpected error: {exc}"
        return [TextContent(type="text", text=text)]

    def _get_backend(args: dict[str, Any]) -> tuple[str, Backend]:
        ds_name = args.get("datasource", "")
        if ds_name not in datasources:
            available = list(datasources.keys())
            raise ValueError(
                f"Unknown datasource: {ds_name!r}. Available: {available}"
            )
        _, backend = datasources[ds_name]
        return ds_name, backend

    def _dispatch(name: str, args: dict[str, Any]) -> str:
        if name == "list_datasources":
            info = []
            for ds_name, (cfg, _) in datasources.items():
                entry: dict[str, Any] = {"name": ds_name, "type": cfg.type}
                if cfg.type == "mysql":
                    entry.update(host=cfg.host, port=cfg.port, database=cfg.database)
                elif cfg.type == "sqlite":
                    entry["path"] = cfg.path
                info.append(entry)
            return json.dumps(info, indent=2)

        ds_name, backend = _get_backend(args)

        if name == "list_tables":
            return json.dumps(backend.list_tables(), indent=2)

        if name == "describe_table":
            table = args.get("table")
            if not table:
                raise ValueError("'table' is required.")
            return json.dumps(backend.describe_table(table), indent=2, default=str)

        if name == "get_create_statement":
            table = args.get("table")
            if not table:
                raise ValueError("'table' is required.")
            return backend.get_create_statement(table)

        if name == "list_foreign_keys":
            return json.dumps(
                backend.list_foreign_keys(args.get("table")), indent=2
            )

        if name == "list_indexes":
            table = args.get("table")
            if not table:
                raise ValueError("'table' is required.")
            return json.dumps(backend.list_indexes(table), indent=2)

        if name == "search_columns":
            pattern = args.get("pattern", "").lower()
            if not pattern:
                raise ValueError("'pattern' is required.")
            matches: list[dict[str, Any]] = []
            for t in backend.list_tables():
                tname = t["table_name"]
                for col in backend.describe_table(tname):
                    if pattern in col["column_name"].lower():
                        matches.append({"table": tname, **col})
            return json.dumps(matches, indent=2, default=str)

        if name == "get_erd":
            tables = backend.list_tables()
            erd: dict[str, Any] = {"datasource": ds_name, "tables": []}
            for t in tables:
                tname = t["table_name"]
                erd["tables"].append({
                    "name": tname,
                    "columns": backend.describe_table(tname),
                    "foreign_keys": backend.list_foreign_keys(tname),
                })
            return json.dumps(erd, indent=2, default=str)

        raise ValueError(f"Unknown tool: {name}")

    return server


async def _run() -> None:
    load_dotenv()
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    datasources = load_datasources()
    if not datasources:
        logger.warning("No datasources configured. Set the DATASOURCES env var.")
    server = build_server(datasources)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
