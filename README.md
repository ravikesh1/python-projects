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

## Stored procedures

The `sql/` directory ships a sample `users` table and four CRUD procedures
(`get_user_by_id`, `upsert_user`, `delete_user`, `list_users`). A small CLI is
included to apply them and call them, driven by the same `MYSQL_*` env vars as
the server:

```bash
uv run mcp-mysql-sql apply sql/schema sql/procedures
uv run mcp-mysql-sql list
uv run mcp-mysql-sql call upsert_user alice@example.com "Alice" 1
uv run mcp-mysql-sql call get_user_by_id 1
```

The runner understands `DELIMITER` directives, so the `.sql` files can be edited
and applied directly without preprocessing.

### VSCode

`.vscode/tasks.json` and `.vscode/launch.json` wrap the same CLI:

- **Run Task → SQL: apply all** — applies schema then procedures.
- **Run Task → SQL: apply current file** — applies the file in the active editor.
- **Run Task → SQL: call procedure** — prompts for the name and args.
- **Run Task → SQL: list routines** — lists procedures/functions in `MYSQL_DATABASE`.
- **Run and Debug** panel offers the same actions under the Python debugger.

Recommended extensions are listed in `.vscode/extensions.json` (SQLTools +
MySQL driver for browsing the DB, Python + debugpy for stepping through the
runner).

## Safety notes

- Writes and DDL are disabled by default; opt in explicitly via env vars.
- The server enforces statement type per tool (e.g. `read_query` rejects anything that isn't a read).
- For production, give the MCP server a MySQL user with the minimum privileges you want it to have. The env flags are a convenience, not a security boundary.
