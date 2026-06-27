# MySQL MCP server evals

A deterministic eval suite that launches `mcp-mysql-server` and drives it as a
**real MCP client** over stdio, exercising every tool and resource against a
**real MySQL** seeded with known data. It scores each case and exits non-zero on
any failure, so it works as a CI gate.

The suite is **gated**: if MySQL is unreachable it prints a message and exits 0
(skipped, not failed), so it's safe to run anywhere.

## What it checks

| Category        | Examples |
| --------------- | -------- |
| `introspection` | `list_databases`, `list_tables`, `describe_table` return the seeded objects |
| `read_query`    | `SELECT` values/counts, `WITH` (CTE) and `EXPLAIN` accepted |
| `truncation`    | `MYSQL_ROW_LIMIT` truncates and sets `truncated: true` |
| `safety`        | `read_query` rejects DML/DDL; `write_query`/`execute_ddl` disabled by default |
| `write`         | `write_query` INSERT affects rows and is then readable |
| `ddl`           | `execute_ddl` CREATE succeeds and shows up in `list_tables` |
| `resources`     | `mysql://<db>/<table>/schema` lists and returns `CREATE TABLE` |
| `serialization` | `DATE`/`DECIMAL`/`BLOB` come back as valid JSON (ISO date, decimal string, utf-8/hex bytes) |
| `errors`        | invalid SQL → `MySQL error:`; unknown tool rejected |

## How it works

The server reads its config (safety flags, row limit) from the environment **at
startup**, so the runner groups cases by the server config they need and launches
one server subprocess per group:

| Group     | Server env |
| --------- | ---------- |
| `default` | read-only, `MYSQL_ROW_LIMIT=1000` |
| `limited` | `MYSQL_ROW_LIMIT=5` |
| `write`   | `MYSQL_ALLOW_WRITE=true` |
| `ddl`     | `MYSQL_ALLOW_DDL=true` |

Seeding and the connectivity gate talk to MySQL directly via PyMySQL (see
`harness.py`); the eval cases only ever go through the MCP client session.

## Running

The MySQL user needs privileges to **CREATE DATABASE / CREATE TABLE / INSERT**
(the suite creates an isolated database, defaulting to `mcp_eval`, and drops it
afterward).

```bash
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=secret

uv run mcp-mysql-evals          # or: uv run python -m evals.run
```

A local MySQL for testing (when a Docker daemon is available):

```bash
docker run --rm -d --name mcp-eval-mysql \
  -e MYSQL_ROOT_PASSWORD=secret -p 3306:3306 mysql:8
```

## Configuration

| Variable        | Default    | Description |
| --------------- | ---------- | ----------- |
| `MYSQL_*`       | see server | Connection settings (reused from the server's config) |
| `MCP_EVAL_DB`   | `mcp_eval` | Name of the isolated database the suite creates |
| `MCP_EVAL_KEEP` | `false`    | Keep the eval database instead of dropping it on teardown |

## Adding cases

Append a `Case` in `evals/cases.py`. Pick the `group` whose server config the
case needs, choose a `kind` (`tool` / `read_resource` / `list_resources`), and a
scorer (`expect_json`, `expect_error`, or a small lambda). No runner changes
needed.
