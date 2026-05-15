"""CLI for applying SQL files and calling stored procedures against MySQL.

Run via uv:

    uv run mcp-mysql-sql apply sql/schema sql/procedures
    uv run mcp-mysql-sql call upsert_user alice@example.com "Alice" 1
    uv run mcp-mysql-sql list

Uses the same MYSQL_* environment variables as the MCP server (see .env.example).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .server import Config, _connect, _json_default


def split_sql_statements(text: str) -> list[str]:
    """Split a SQL script into individual statements, honoring DELIMITER directives.

    Handles the common `DELIMITER $$ ... END$$ DELIMITER ;` pattern used to define
    stored procedures. Does not try to parse strings or comments, which is fine for
    well-formed procedure files but not a general-purpose SQL parser.
    """
    delimiter = ";"
    statements: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("DELIMITER "):
            sql = "\n".join(current).strip()
            if sql:
                statements.append(sql)
            current = []
            delimiter = stripped.split(None, 1)[1].strip()
            continue
        if line.rstrip().endswith(delimiter):
            current.append(line.rstrip()[: -len(delimiter)])
            sql = "\n".join(current).strip()
            if sql:
                statements.append(sql)
            current = []
        else:
            current.append(line)
    tail = "\n".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def _collect_sql_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(sorted(path.rglob("*.sql")))
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(f"No such SQL path: {path}")
    return files


def cmd_apply(cfg: Config, paths: list[str]) -> int:
    files = _collect_sql_files(paths)
    if not files:
        print("no .sql files found", file=sys.stderr)
        return 1
    conn = _connect(cfg)
    try:
        with conn.cursor() as cur:
            for f in files:
                print(f"-- applying {f}", file=sys.stderr)
                for stmt in split_sql_statements(f.read_text(encoding="utf-8")):
                    cur.execute(stmt)
    finally:
        conn.close()
    return 0


def cmd_call(cfg: Config, procedure: str, args: list[str]) -> int:
    placeholders = ", ".join(["%s"] * len(args))
    sql = f"CALL `{procedure}`({placeholders})"
    conn = _connect(cfg)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(args))
            result_sets: list[Any] = []
            while True:
                if cur.description is not None:
                    result_sets.append(list(cur.fetchall()))
                else:
                    result_sets.append({"affected_rows": cur.rowcount})
                if not cur.nextset():
                    break
        print(json.dumps(result_sets, default=_json_default, indent=2))
    finally:
        conn.close()
    return 0


def cmd_list(cfg: Config) -> int:
    if not cfg.database:
        raise ValueError("MYSQL_DATABASE must be set to list routines.")
    conn = _connect(cfg)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT routine_name, routine_type, created, last_altered "
                "FROM information_schema.routines "
                "WHERE routine_schema = %s "
                "ORDER BY routine_type, routine_name",
                (cfg.database,),
            )
            rows = list(cur.fetchall())
        print(json.dumps(rows, default=_json_default, indent=2))
    finally:
        conn.close()
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mcp-mysql-sql",
        description="Apply SQL files and invoke stored procedures.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    apply_p = sub.add_parser("apply", help="Apply one or more .sql files or directories.")
    apply_p.add_argument("paths", nargs="+", help="SQL files or directories to apply (in order).")

    call_p = sub.add_parser("call", help="CALL a stored procedure with positional args.")
    call_p.add_argument("procedure", help="Procedure name.")
    call_p.add_argument("args", nargs="*", help="Positional arguments passed as strings.")

    sub.add_parser("list", help="List stored routines in MYSQL_DATABASE.")
    return parser


def main() -> int:
    load_dotenv()
    parser = _build_parser()
    ns = parser.parse_args()
    cfg = Config.from_env()
    if ns.command == "apply":
        return cmd_apply(cfg, ns.paths)
    if ns.command == "call":
        return cmd_call(cfg, ns.procedure, ns.args)
    if ns.command == "list":
        return cmd_list(cfg)
    parser.error(f"unknown command: {ns.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
