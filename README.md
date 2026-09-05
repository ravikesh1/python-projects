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

## Sample schema

The `schema/` directory ships a small e-commerce demo schema
(`users`, `products`, `orders`, `order_items`) so the server has something
concrete to inspect and query. The column names line up with the example queries
in the `mysql-explorer` skill, so those work as-is against this data.

```bash
mysql -h "$MYSQL_HOST" -u "$MYSQL_USER" -p "$MYSQL_DATABASE" < schema/schema.sql
mysql -h "$MYSQL_HOST" -u "$MYSQL_USER" -p "$MYSQL_DATABASE" < schema/seed.sql   # optional sample rows
```

`schema.sql` uses `CREATE TABLE IF NOT EXISTS` (InnoDB, `utf8mb4`); `seed.sql`
inserts a handful of rows with explicit ids for a fresh database.

## Skill: mysql-explorer

This repo also ships a companion **Agent Skill** (`skills/mysql-explorer/`) that
teaches Claude how to drive the MCP tools above safely — discover schemas first,
respect the row cap, and treat writes/DDL as deliberate, confirmed actions.

> For the full step-by-step publish workflow (and the desktop vs. Claude Code
> differences), see [PUBLISHING.md](PUBLISHING.md).

### Publish it to the Claude desktop app

The Claude desktop chat app installs skills by **uploading a `.zip`** — it does
not connect to or auto-sync from GitHub. So the flow is build-then-upload:

```bash
bash skills/build.sh        # produces dist/mysql-explorer.zip
```

Then in the desktop app: **Settings → Capabilities → Skills → Upload** and select
`dist/mysql-explorer.zip`. (Code Execution must be enabled.)

When you change the skill, re-run the build and re-upload — there is no automatic
sync from the repo to the app.

### Install it in Claude Code (GitHub-linked, auto-updating)

For **Claude Code** (CLI/IDE), this repo doubles as a plugin marketplace, so the
same skill installs straight from GitHub and updates when you push:

```text
/plugin marketplace add ravikesh1/python-projects
/plugin install mysql-explorer@ravikesh-python-projects
```

Refresh later with `/plugin marketplace update`. The marketplace and plugin
manifests live in `.claude-plugin/`, and the plugin reuses the same
`skills/mysql-explorer/` folder as the desktop zip — one source of truth for both.

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

## Evals

A deterministic eval suite drives this server as a real MCP client against a real
(seeded) MySQL and scores every tool/resource. It's gated — it skips cleanly when
MySQL is unavailable, so it's safe to run anywhere:

```bash
uv run mcp-mysql-evals
```

See [`evals/README.md`](evals/README.md) for what it checks and how to point it at
a database.

## Session activity logging

Local hooks in `.claude/` record what each Claude Code session actually did in
this repo — which skills were invoked and every call to a MySQL MCP server.
Configured in `.claude/settings.json`, implemented by
`.claude/hooks/log_session_activity.py`, and appended as JSON lines to
`.claude/logs/session-activity.jsonl` (gitignored — local machine state, never
shipped with the plugin/skill).

The hook events that feed it:

| Event | Record | What it captures |
| --- | --- | --- |
| `SessionStart` | `session_start` | session id, cwd, start source (`startup` / `resume` / `clear` / `compact`), transcript path |
| `PostToolUse` (`Skill`) | `skill` | skill name, args, invocation level (`user_invoked` when you typed `/<skill>`, `model_invoked` when Claude loaded it itself), invocation number within the session, and the user prompt that triggered it |
| `PostToolUse` (`mcp__*mysql*__*`) | `mcp_tool` | server, tool, database/table, the SQL statement (truncated to 500 chars), and a result summary: `ok`, `row_count`, `truncated`, `affected_rows`, or `error` |
| `SessionEnd` | `session_end` | end reason plus a rollup: skill invocations, skills used, MCP calls, servers/tools used, failure count |

The `PostToolUse` matcher is `Skill|mcp__.*mysql.*`, so any MCP server whose
name contains "mysql" is logged; other MCP servers and ordinary tools are
ignored. The hook swallows every error and always exits 0 — it can never block
a tool call or break a session.

### Reading the log

```bash
python3 .claude/hooks/session_report.py                 # rollup of recent sessions
python3 .claude/hooks/session_report.py --limit 20      # more sessions
python3 .claude/hooks/session_report.py --session <id>  # full timeline for one session
python3 .claude/hooks/session_report.py --json          # machine-readable output
```

Example:

```
session sess_01ABC
  started : 2026-09-05T17:59:16+00:00
  ended   : 2026-09-05T18:24:02+00:00
  cwd     : /home/you/python-projects
  skills  : 1 invocation(s) [user 1 / model 0] -> mysql-explorer
  mcp     : 2 call(s), 1 failure(s) -> mysql [describe_table, read_query]
```

## Safety notes

- Writes and DDL are disabled by default; opt in explicitly via env vars.
- The server enforces statement type per tool (e.g. `read_query` rejects anything that isn't a read).
- For production, give the MCP server a MySQL user with the minimum privileges you want it to have. The env flags are a convenience, not a security boundary.
