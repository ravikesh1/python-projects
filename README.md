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

## LangChain Tag System

A second tool in this repo: a small LangChain/LangGraph-powered tagger.

- `Tagger` — wraps a Claude model with `with_structured_output` and a Pydantic `Tags` schema (sentiment, language, aggressiveness, topics).
- `tag_system.store` — JSON-backed store (`.tag_store.json` by default, override with `TAG_STORE_PATH`).
- `tag_system.agent` — LangGraph ReAct agent exposing four tools: `tag_text`, `save_tagged`, `search_topic`, `list_all`. Orchestrate the workflow with a natural-language instruction.

Set `ANTHROPIC_API_KEY` (and optionally `TAG_MODEL`) before running.

```bash
# One-shot structured tagging
uv run tag-text "I absolutely loved the new release, it was a delight."

# Agentic workflow — give it an instruction, it picks the tools
uv run tag-agent "Tag and save this: I hate Mondays."
uv run tag-agent "Show me everything tagged with 'release'."
```

Programmatic use:

```python
from tag_system import Tagger
from tag_system.agent import build_agent
from langchain_core.messages import HumanMessage

tags = Tagger().tag("Es un día maravilloso.")
print(tags.language, tags.sentiment, tags.topics)

agent = build_agent()
out = agent.invoke({"messages": [HumanMessage(content="tag and save: ship it")]})
print(out["messages"][-1].content)
```

## Safety notes

- Writes and DDL are disabled by default; opt in explicitly via env vars.
- The server enforces statement type per tool (e.g. `read_query` rejects anything that isn't a read).
- For production, give the MCP server a MySQL user with the minimum privileges you want it to have. The env flags are a convenience, not a security boundary.
