"""Test harness: MySQL gating/seeding and an MCP client session for the server.

Seeding and the connectivity gate talk to MySQL directly via PyMySQL. The evals
themselves never touch the database directly -- they go through a real MCP client
session connected to a freshly launched ``mcp-mysql-server`` subprocess.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import pymysql
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = Path(__file__).resolve().parent / "fixtures" / "seed.sql"

# Default eval database. Isolated from any real data; created and dropped by the
# harness. Override with MCP_EVAL_DB.
DEFAULT_EVAL_DB = "mcp_eval"


def eval_db() -> str:
    return os.getenv("MCP_EVAL_DB", DEFAULT_EVAL_DB)


def keep_db() -> bool:
    return os.getenv("MCP_EVAL_KEEP", "").strip().lower() in ("1", "true", "yes", "on")


def base_env() -> dict[str, str]:
    """Connection settings shared by every server subprocess and by seeding.

    Mirrors the defaults in ``Config.from_env`` (mcp_mysql_server/server.py) so
    the harness and the server agree on where MySQL lives.
    """
    return {
        "MYSQL_HOST": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "MYSQL_PORT": os.getenv("MYSQL_PORT", "3306"),
        "MYSQL_USER": os.getenv("MYSQL_USER", "root"),
        "MYSQL_PASSWORD": os.getenv("MYSQL_PASSWORD", ""),
        "MYSQL_CHARSET": os.getenv("MYSQL_CHARSET", "utf8mb4"),
    }


def _connect(database: str | None = None) -> pymysql.connections.Connection:
    env = base_env()
    return pymysql.connect(
        host=env["MYSQL_HOST"],
        port=int(env["MYSQL_PORT"]),
        user=env["MYSQL_USER"],
        password=env["MYSQL_PASSWORD"],
        database=database,
        charset=env["MYSQL_CHARSET"],
        autocommit=True,
        connect_timeout=5,
    )


def mysql_available() -> bool:
    """True if a MySQL server is reachable with the configured credentials."""
    try:
        conn = _connect()
    except Exception:
        return False
    conn.close()
    return True


def _split_statements(sql: str) -> list[str]:
    """Split a SQL script into individual statements.

    Drops ``--`` line comments and blank lines, then splits on ``;``. The seed
    script deliberately avoids semicolons inside string literals so this stays
    simple and dependency-free.
    """
    lines = [ln for ln in sql.splitlines() if not ln.lstrip().startswith("--")]
    body = "\n".join(lines)
    return [stmt.strip() for stmt in body.split(";") if stmt.strip()]


def seed_database() -> None:
    """(Re)create the eval database and load the known schema + data."""
    script = SEED_PATH.read_text().replace("{db}", eval_db())
    conn = _connect()  # no default DB: the script creates and selects it
    try:
        with conn.cursor() as cur:
            for stmt in _split_statements(script):
                cur.execute(stmt)
    finally:
        conn.close()


def teardown_database() -> None:
    """Drop the eval database unless MCP_EVAL_KEEP is set."""
    if keep_db():
        return
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS `{eval_db()}`")
    finally:
        conn.close()


@asynccontextmanager
async def mcp_session(env_overrides: dict[str, str] | None = None) -> AsyncIterator[ClientSession]:
    """Launch the MCP server pointed at the eval DB and yield a client session.

    ``env_overrides`` sets per-group server config (e.g. MYSQL_ALLOW_WRITE,
    MYSQL_ROW_LIMIT). The full process env is inherited so ``uv`` resolves on
    PATH; MySQL settings are then overridden explicitly.
    """
    env = {**os.environ, **base_env(), "MYSQL_DATABASE": eval_db()}
    if env_overrides:
        env.update(env_overrides)

    params = StdioServerParameters(
        command="uv",
        args=["run", "mcp-mysql-server"],
        env=env,
        cwd=str(PROJECT_ROOT),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


def load_local_env() -> None:
    """Load a .env file if present so local runs pick up MYSQL_* settings."""
    load_dotenv()
