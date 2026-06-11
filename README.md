# python-projects

Small Python projects, managed with [uv](https://docs.astral.sh/uv/):

- **[Gas Tracker](gas_tracker/README.md)** – CLI that finds gas stations near a
  location (defaults to Surrey, BC) and ranks them cheapest-first, with a live
  watch mode (`uv run gas-tracker`)
- **MCP MySQL Server** – MCP server for inspecting and querying MySQL
  (documented below)

---

# MCP MySQL Server

A Model Context Protocol (MCP) server that lets an MCP-compatible client (Claude Desktop, Claude Code, etc.) inspect and query a MySQL database.

## Features

- `list_databases` – list databases visible to the configured user
- `list_tables` – list tables in a database (with type/engine/row estimate)
- `describe_table` – return column metadata for a table
- `read_query` – execute read-only SQL (`SELECT` / `SHOW` / `DESCRIBE` / `EXPLAIN` / `WITH`)
- `write_query` – execute DML (`INSERT` / `UPDATE` / `DELETE` / `REPLACE`), opt-in via `MYSQL_ALLOW_WRITE=true`
- `execute_ddl` – execute DDL (`CREATE` / `ALTER` / `DROP` / `TRUNCATE` / `RENAME`), opt-in via `MYSQL_ALLOW_DDL=true`
- Resources – exposes `mysql://<database>/<table>/schema` so clients can pull `CREATE TABLE` statements

Reads are capped at `MYSQL_ROW_LIMIT` rows (default 1000) and results are returned as JSON with a `truncated` flag.

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for environment and dependency management.

```bash
uv sync
```

That creates a `.venv` from `uv.lock` and installs the `mcp-mysql-server` script. Requires Python 3.10+ (uv will fetch it if missing).

## Configuration

Copy `.env.example` to `.env` and fill it in, or export the variables in your shell / MCP client config:

| Variable             | Default     | Description                                  |
| -------------------- | ----------- | -------------------------------------------- |
| `MYSQL_HOST`         | `127.0.0.1` | MySQL host                                   |
| `MYSQL_PORT`         | `3306`      | MySQL port                                   |
| `MYSQL_USER`         | `root`      | MySQL user                                   |
| `MYSQL_PASSWORD`     |             | MySQL password                               |
| `MYSQL_DATABASE`     |             | Default database (optional)                  |
| `MYSQL_CHARSET`      | `utf8mb4`   | Connection charset                           |
| `MYSQL_ALLOW_WRITE`  | `false`     | Expose `write_query` tool                    |
| `MYSQL_ALLOW_DDL`    | `false`     | Expose `execute_ddl` tool                    |
| `MYSQL_ROW_LIMIT`    | `1000`      | Maximum rows returned per query              |
| `LOG_LEVEL`          | `INFO`      | Python log level                             |

## Running

```bash
uv run mcp-mysql-server
```

The server speaks MCP over stdio.

## Claude Desktop / Claude Code config

Add an entry to your `mcp` config (e.g. `~/.claude/mcp.json` or `claude_desktop_config.json`). Using `uv run` keeps the server isolated in its own env:

```json
{
  "mcpServers": {
    "mysql": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/python-projects",
        "run",
        "mcp-mysql-server"
      ],
      "env": {
        "MYSQL_HOST": "127.0.0.1",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "readonly",
        "MYSQL_PASSWORD": "secret",
        "MYSQL_DATABASE": "myapp"
      }
    }
  }
}
```

Or run directly from a Git checkout without installing globally:

```bash
uvx --from git+https://github.com/<you>/python-projects mcp-mysql-server
```

## Safety notes

- Writes and DDL are disabled by default; opt in explicitly via env vars.
- The server enforces statement type per tool (e.g. `read_query` rejects anything that isn't a read).
- For production, give the MCP server a MySQL user with the minimum privileges you want it to have. The env flags are a convenience, not a security boundary.
