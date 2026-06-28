---
name: mysql-explorer
description: Use when inspecting or querying a MySQL database through the mcp-mysql-server MCP tools — discovering databases and tables, reading schemas, writing safe read-only SQL, and deliberately opting into writes or DDL. Triggers on requests to explore, query, or modify a MySQL database that is connected via this MCP server.
---

# MySQL Explorer

Guidance for working with a MySQL database through the **mcp-mysql-server** MCP
tools (`list_databases`, `list_tables`, `describe_table`, `read_query`,
`write_query`, `execute_ddl`) and the `mysql://<database>/<table>/schema`
resources.

## When to use this skill

Use it whenever the user wants to explore a schema, read data, or change data in a
MySQL database reachable through the connected MCP server. If the MySQL MCP tools
are not available in the session, tell the user the server isn't connected rather
than guessing.

## Core workflow

1. **Discover before querying.** Don't assume table or column names.
   - `list_databases` → pick the database.
   - `list_tables` → see tables, types, engines, and row estimates.
   - `describe_table` → confirm exact column names and types before writing SQL.
   - When you need the full DDL, read the `mysql://<database>/<table>/schema`
     resource to get the `CREATE TABLE` statement.

2. **Read with `read_query`.** It accepts read-only statements only
   (`SELECT` / `SHOW` / `DESCRIBE` / `EXPLAIN` / `WITH`). The server rejects
   anything else, so don't try to sneak writes through it.

3. **Respect the row cap.** Results are capped at `MYSQL_ROW_LIMIT` (default 1000)
   and come back as JSON with a `truncated` flag. If `truncated` is `true`, the
   result is incomplete — add an explicit `LIMIT`, paginate with
   `LIMIT ... OFFSET ...`, or aggregate (`COUNT`, `GROUP BY`) instead of assuming
   you saw every row.

4. **Writes and DDL are opt-in and gated.**
   - `write_query` (`INSERT` / `UPDATE` / `DELETE` / `REPLACE`) only exists when
     `MYSQL_ALLOW_WRITE=true`.
   - `execute_ddl` (`CREATE` / `ALTER` / `DROP` / `TRUNCATE` / `RENAME`) only
     exists when `MYSQL_ALLOW_DDL=true`.
   - If the tool isn't present, the operator hasn't enabled it — say so instead of
     working around it.
   - Before any destructive or mutating statement, restate what it will change and
     confirm intent with the user. Prefer a `SELECT` preview of affected rows first.

## Safety defaults

- Default to read-only. Treat mutation as a deliberate, confirmed action.
- Never paper over a rejected statement by reclassifying it to a different tool.
- For repeated or large reads, prefer aggregates over pulling raw rows.

See `reference.md` for a per-tool cheat-sheet and ready-to-adapt query patterns.
