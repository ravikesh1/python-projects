# MySQL Explorer — Reference

Cheat-sheet for the `mcp-mysql-server` MCP tools and common query patterns.
Argument names below match the server's tool schemas exactly.

## Tools

| Tool | Arguments | Notes |
| --- | --- | --- |
| `list_databases` | _(none)_ | Lists databases visible to the configured user. |
| `list_tables` | `database` _(optional)_ | Falls back to `MYSQL_DATABASE` if omitted. Returns type/engine/row estimate. |
| `describe_table` | `table` _(required)_, `database` _(optional)_ | Column definitions for one table. |
| `read_query` | `sql` _(required)_ | Read-only: `SELECT` / `SHOW` / `DESCRIBE` / `EXPLAIN` / `WITH`. Capped at `MYSQL_ROW_LIMIT` rows. |
| `write_query` | `sql` _(required)_ | Only present when `MYSQL_ALLOW_WRITE=true`. `INSERT` / `UPDATE` / `DELETE` / `REPLACE`. Returns affected row count. |
| `execute_ddl` | `sql` _(required)_ | Only present when `MYSQL_ALLOW_DDL=true`. `CREATE` / `ALTER` / `DROP` / `TRUNCATE` / `RENAME`. |

## Resources

- `mysql://<database>/<table>/schema` → the `CREATE TABLE` statement for that table.
  Use it when you need exact DDL, indexes, or constraints rather than just column types.

## Result shape

`read_query` returns JSON: a list of row objects plus a `truncated` flag.
When `truncated` is `true`, you did **not** see all matching rows — narrow the query.

## Query patterns

**Explore a schema safely**
```
list_databases
list_tables            (database: "myapp")
describe_table         (table: "orders", database: "myapp")
```

**Bounded read instead of a blind SELECT**
```sql
SELECT id, status, created_at
FROM orders
WHERE created_at >= '2026-01-01'
ORDER BY created_at DESC
LIMIT 200;
```

**Aggregate rather than pulling raw rows (avoids truncation)**
```sql
SELECT status, COUNT(*) AS n
FROM orders
GROUP BY status;
```

**Paginate past the row cap**
```sql
SELECT id, email FROM users ORDER BY id LIMIT 1000 OFFSET 1000;
```

**Preview before a write (run as a read first)**
```sql
-- 1) read_query: see exactly what would change
SELECT id, status FROM orders WHERE status = 'pending' AND created_at < '2025-01-01';
-- 2) write_query: only after confirming intent
UPDATE orders SET status = 'expired'
WHERE status = 'pending' AND created_at < '2025-01-01';
```

## Reminders

- Reads default. Writes/DDL are deliberate, confirmed, and may simply be unavailable
  (the operator controls `MYSQL_ALLOW_WRITE` / `MYSQL_ALLOW_DDL`).
- Never re-route a rejected statement to a different tool to bypass the type check.
- If a mutation has no `WHERE`, stop and confirm — it will affect every row.
