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

---

# AI Knowledge Agent ("Batcomputer")

A web-research knowledge system: it searches the web, ingests pages into a local
knowledge base, and lets you query that knowledge to help you build things —
like a personal Batcomputer. The knowledge core is shared and exposed two ways:

- **MCP server** (`ai-knowledge-mcp`) — plug it into Claude Desktop / Claude
  Code so Claude itself can search, ingest, and query the knowledge base. No
  API key required.
- **Standalone CLI agent** (`ai-knowledge-agent`) — a terminal REPL that runs
  its own Claude-powered agent loop over the same tools. Requires
  `ANTHROPIC_API_KEY`.

## How it works

- **Storage** — SQLite with FTS5 full-text search (falls back to `LIKE` if a
  SQLite build lacks FTS5). Fully local, no extra services.
- **Sources** — web pages and web search (DuckDuckGo, keyless). Pages are
  fetched with `httpx` and reduced to clean article text with `trafilatura`.
- **Retrieval** — keyword / full-text search ranked with BM25, returning
  highlighted snippets.

The core is source-agnostic, so adding arXiv, local PDFs, or manual notes later
is a small addition — no schema changes.

## Tools

| Tool               | Description                                                     |
| ------------------ | ------------------------------------------------------------- |
| `web_search`       | Search the web; returns title/url/snippet (stores nothing).   |
| `ingest_url`       | Fetch a URL, extract text, store it in the knowledge base.    |
| `ingest_search`    | Search the web and ingest the top results.                    |
| `search_knowledge` | Full-text search across stored documents.                     |
| `get_document`     | Retrieve a stored document's full text by id.                 |
| `list_documents`   | List recently ingested documents.                             |
| `delete_document`  | Remove a document by id (MCP only).                           |
| `knowledge_stats`  | Document count, total size, and backend info.                 |

## Configuration

All settings have defaults; override via `.env` or the environment:

| Variable                       | Default                              | Description                                   |
| ------------------------------ | ------------------------------------ | --------------------------------------------- |
| `KNOWLEDGE_DB_PATH`            | `~/.ai_knowledge_agent/knowledge.db` | SQLite knowledge-base path                    |
| `KNOWLEDGE_SEARCH_MAX_RESULTS` | `5`                                  | Default web/knowledge result count            |
| `KNOWLEDGE_INGEST_MAX_CHARS`   | `50000`                              | Max characters stored per ingested page       |
| `KNOWLEDGE_REQUEST_TIMEOUT`    | `30`                                 | HTTP fetch timeout (seconds)                  |
| `KNOWLEDGE_MODEL`              | `claude-opus-4-8`                    | Claude model used by the CLI agent            |
| `ANTHROPIC_API_KEY`            |                                      | Required by the CLI agent only                |

## Running the CLI agent

```bash
export ANTHROPIC_API_KEY=sk-ant-...
uv run ai-knowledge-agent
```

Then ask research questions; the agent searches, ingests sources, and answers
grounded in what it stored. Type `exit` to quit.

## Running the MCP server

```bash
uv run ai-knowledge-mcp
```

It speaks MCP over stdio. Claude Desktop / Claude Code config:

```json
{
  "mcpServers": {
    "knowledge": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/python-projects",
        "run",
        "ai-knowledge-mcp"
      ],
      "env": {
        "KNOWLEDGE_DB_PATH": "/absolute/path/to/knowledge.db"
      }
    }
  }
}
```

> Note: web search and page fetching require outbound internet access from
> wherever the server/agent runs.
