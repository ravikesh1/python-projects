"""Declarative eval cases and scorers for the MySQL MCP server.

Each :class:`Case` names the server config group it needs (which determines the
server subprocess it runs against), how to invoke the server, and a ``check``
that scores the result. ``check`` receives:

- a decoded ``str`` for ``tool`` and ``read_resource`` cases (the server's
  ``TextContent`` payload), or
- a ``list`` of resource descriptors for ``list_resources`` cases.

It returns ``(passed, detail)`` where ``detail`` explains a failure (or
summarizes a pass).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

# Server config groups -> per-group env overrides for the server subprocess.
GROUP_ENV: dict[str, dict[str, str]] = {
    "default": {},
    "limited": {"MYSQL_ROW_LIMIT": "5"},
    "write": {"MYSQL_ALLOW_WRITE": "true"},
    "ddl": {"MYSQL_ALLOW_DDL": "true"},
}


@dataclass
class Case:
    name: str
    category: str
    group: str
    kind: str  # "tool" | "read_resource" | "list_resources"
    check: Callable[[Any], tuple[bool, str]]
    tool: str | None = None
    args: dict[str, Any] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Scorer helpers
# --------------------------------------------------------------------------- #

def _parse(text: str) -> dict[str, Any]:
    return json.loads(text)


def _rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return payload.get("rows", [])


def _all_values(rows: list[dict[str, Any]]) -> set[str]:
    return {str(v) for row in rows for v in row.values()}


def expect_json(predicate: Callable[[dict[str, Any]], bool], desc: str) -> Callable[[Any], tuple[bool, str]]:
    """Parse the payload as JSON and run ``predicate`` over it."""
    def check(text: Any) -> tuple[bool, str]:
        try:
            payload = _parse(text)
        except (json.JSONDecodeError, TypeError):
            return False, f"expected JSON ({desc}); got: {str(text)[:200]!r}"
        try:
            ok = predicate(payload)
        except Exception as exc:  # noqa: BLE001
            return False, f"{desc}: predicate raised {exc!r}; payload={text[:200]}"
        return ok, desc if ok else f"failed: {desc}; payload={text[:300]}"
    return check


def expect_error(substring: str) -> Callable[[Any], tuple[bool, str]]:
    """Assert the payload is an error string containing ``substring``."""
    def check(text: Any) -> tuple[bool, str]:
        ok = isinstance(text, str) and substring in text
        return ok, f"contains {substring!r}" if ok else f"expected error {substring!r}; got: {str(text)[:300]!r}"
    return check


def values_contain(*needles: str) -> Callable[[dict[str, Any]], bool]:
    def predicate(payload: dict[str, Any]) -> bool:
        vals = _all_values(_rows(payload))
        return all(any(n == v or n in v for v in vals) for n in needles)
    return predicate


# --------------------------------------------------------------------------- #
# Cases
# --------------------------------------------------------------------------- #

EVAL_DB_PLACEHOLDER = "{db}"  # replaced with the real eval DB name at runtime


def build_cases(db: str) -> list[Case]:
    """Build the case list, binding resource URIs to the real eval DB name."""

    cases: list[Case] = [
        # ---- introspection ------------------------------------------------ #
        Case(
            name="list_databases includes eval DB",
            category="introspection", group="default", kind="tool",
            tool="list_databases", args={},
            check=expect_json(values_contain(db), f"databases include {db}"),
        ),
        Case(
            name="list_tables returns users + orders",
            category="introspection", group="default", kind="tool",
            tool="list_tables", args={},
            check=expect_json(values_contain("users", "orders"), "tables include users, orders"),
        ),
        Case(
            name="describe_table users has expected columns",
            category="introspection", group="default", kind="tool",
            tool="describe_table", args={"table": "users"},
            check=expect_json(
                values_contain("id", "name", "email", "created_at", "balance", "active"),
                "users columns present",
            ),
        ),

        # ---- read_query --------------------------------------------------- #
        Case(
            name="read_query SELECT count",
            category="read_query", group="default", kind="tool",
            tool="read_query", args={"sql": "SELECT COUNT(*) AS c FROM users"},
            check=expect_json(lambda p: _rows(p)[0].get("c") == 22, "count(users) == 22"),
        ),
        Case(
            name="read_query SELECT row values",
            category="read_query", group="default", kind="tool",
            tool="read_query", args={"sql": "SELECT name, email FROM users WHERE id = 1"},
            check=expect_json(
                lambda p: _rows(p)[0].get("name") == "Alice"
                and _rows(p)[0].get("email") == "alice@example.com",
                "user 1 is Alice",
            ),
        ),
        Case(
            name="read_query WITH (CTE) accepted",
            category="read_query", group="default", kind="tool",
            tool="read_query", args={"sql": "WITH t AS (SELECT 1 AS n) SELECT n FROM t"},
            check=expect_json(lambda p: _rows(p)[0].get("n") == 1, "CTE returns n == 1"),
        ),
        Case(
            name="read_query EXPLAIN accepted",
            category="read_query", group="default", kind="tool",
            tool="read_query", args={"sql": "EXPLAIN SELECT * FROM users"},
            check=expect_json(lambda p: p.get("row_count", 0) >= 1, "EXPLAIN returns plan rows"),
        ),

        # ---- truncation (row limit) -------------------------------------- #
        Case(
            name="row limit truncates results",
            category="truncation", group="limited", kind="tool",
            tool="read_query", args={"sql": "SELECT id FROM users ORDER BY id"},
            check=expect_json(
                lambda p: p.get("truncated") is True and p.get("row_count") == 5,
                "truncated to 5 rows",
            ),
        ),

        # ---- safety boundary --------------------------------------------- #
        Case(
            name="read_query rejects INSERT",
            category="safety", group="default", kind="tool",
            tool="read_query",
            args={"sql": "INSERT INTO users (name, email, created_at) VALUES ('x','x','2024-01-01')"},
            check=expect_error("read_query only accepts"),
        ),
        Case(
            name="read_query rejects CREATE",
            category="safety", group="default", kind="tool",
            tool="read_query", args={"sql": "CREATE TABLE nope (id INT)"},
            check=expect_error("read_query only accepts"),
        ),
        Case(
            name="write_query disabled by default",
            category="safety", group="default", kind="tool",
            tool="write_query", args={"sql": "INSERT INTO users (name) VALUES ('x')"},
            check=expect_error("Writes are disabled"),
        ),
        Case(
            name="execute_ddl disabled by default",
            category="safety", group="default", kind="tool",
            tool="execute_ddl", args={"sql": "CREATE TABLE nope (id INT)"},
            check=expect_error("DDL is disabled"),
        ),

        # ---- write_query (opt-in) ---------------------------------------- #
        Case(
            name="write_query INSERT affects one row",
            category="write", group="write", kind="tool",
            tool="write_query",
            args={"sql": "INSERT INTO users (name, email, created_at, balance, active) "
                         "VALUES ('Zoe','zoe@example.com','2024-05-01',9.99,1)"},
            check=expect_json(lambda p: _rows(p)[0].get("affected_rows") == 1, "1 row affected"),
        ),
        Case(
            name="inserted row is readable",
            category="write", group="write", kind="tool",
            tool="read_query", args={"sql": "SELECT COUNT(*) AS c FROM users WHERE name = 'Zoe'"},
            check=expect_json(lambda p: _rows(p)[0].get("c") == 1, "Zoe is present"),
        ),
        Case(
            name="write_query rejects SELECT",
            category="write", group="write", kind="tool",
            tool="write_query", args={"sql": "SELECT 1"},
            check=expect_error("write_query only accepts"),
        ),

        # ---- execute_ddl (opt-in) ---------------------------------------- #
        Case(
            name="execute_ddl CREATE TABLE succeeds",
            category="ddl", group="ddl", kind="tool",
            tool="execute_ddl", args={"sql": "CREATE TABLE eval_tmp (id INT PRIMARY KEY)"},
            check=expect_json(lambda p: "rows" in p, "DDL executed without error"),
        ),
        Case(
            name="created table appears in list_tables",
            category="ddl", group="ddl", kind="tool",
            tool="list_tables", args={},
            check=expect_json(values_contain("eval_tmp"), "eval_tmp listed"),
        ),

        # ---- resources ---------------------------------------------------- #
        Case(
            name="list_resources includes users schema",
            category="resources", group="default", kind="list_resources",
            check=lambda resources: (
                (any(str(r.uri).endswith("/users/schema") for r in resources),
                 "users schema resource present")
            ),
        ),
        Case(
            name="read_resource returns CREATE TABLE",
            category="resources", group="default", kind="read_resource",
            args={"uri": f"mysql://{db}/users/schema"},
            check=lambda text: ("CREATE TABLE" in text, "CREATE TABLE in schema")
            if isinstance(text, str) else (False, f"non-text: {text!r}"),
        ),

        # ---- serialization ------------------------------------------------ #
        Case(
            name="DECIMAL and BLOB serialize correctly",
            category="serialization", group="default", kind="tool",
            tool="read_query", args={"sql": "SELECT id, amount, payload FROM orders ORDER BY id"},
            check=expect_json(
                lambda p: _rows(p)[0].get("amount") == "19.99"
                and _rows(p)[0].get("payload") == "hello"
                and _rows(p)[1].get("payload") == "00ff00ff",
                "decimal->str, utf8 blob, hex blob",
            ),
        ),
        Case(
            name="DATE serializes as ISO string",
            category="serialization", group="default", kind="tool",
            tool="read_query", args={"sql": "SELECT created_at FROM users WHERE id = 1"},
            check=expect_json(lambda p: _rows(p)[0].get("created_at") == "2024-01-15", "ISO date"),
        ),

        # ---- error handling ----------------------------------------------- #
        Case(
            name="invalid SQL returns MySQL error",
            category="errors", group="default", kind="tool",
            tool="read_query", args={"sql": "SELECT * FROM table_that_does_not_exist"},
            check=expect_error("MySQL error"),
        ),
        Case(
            name="unknown tool is rejected",
            category="errors", group="default", kind="tool",
            tool="does_not_exist", args={},
            check=expect_error("Unknown tool"),
        ),
    ]
    return cases
