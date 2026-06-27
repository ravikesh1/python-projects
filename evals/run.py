"""Eval runner: gate on MySQL, seed, drive the server, score, report.

Usage:
    uv run mcp-mysql-evals          # or: uv run python -m evals.run

Exit codes:
    0  all cases passed, or MySQL unavailable (skipped)
    1  one or more cases failed
"""

from __future__ import annotations

import asyncio
import sys
from collections import defaultdict
from dataclasses import dataclass

from .cases import GROUP_ENV, Case, build_cases
from .harness import (
    eval_db,
    load_local_env,
    mcp_session,
    mysql_available,
    seed_database,
    teardown_database,
)


@dataclass
class Result:
    case: Case
    passed: bool
    detail: str


def _text_from_call(result) -> str:
    """Join the text blocks of a CallToolResult into a single string."""
    parts = [getattr(b, "text", "") for b in getattr(result, "content", [])]
    return "".join(parts)


def _text_from_resource(result) -> str:
    """Join the text contents of a ReadResourceResult into a single string."""
    parts = [getattr(c, "text", "") for c in getattr(result, "contents", [])]
    return "".join(parts)


async def _run_case(session, case: Case) -> Result:
    try:
        if case.kind == "tool":
            raw = await session.call_tool(case.tool, case.args)
            payload = _text_from_call(raw)
        elif case.kind == "read_resource":
            raw = await session.read_resource(case.args["uri"])
            payload = _text_from_resource(raw)
        elif case.kind == "list_resources":
            raw = await session.list_resources()
            payload = list(getattr(raw, "resources", []))
        else:
            return Result(case, False, f"unknown case kind: {case.kind}")
    except Exception as exc:  # noqa: BLE001
        return Result(case, False, f"invocation raised {exc!r}")

    try:
        passed, detail = case.check(payload)
    except Exception as exc:  # noqa: BLE001
        return Result(case, False, f"check raised {exc!r}")
    return Result(case, bool(passed), detail)


async def _run_all(cases: list[Case]) -> list[Result]:
    results: list[Result] = []
    # Run group by group; each group is one freshly configured server subprocess.
    for group in GROUP_ENV:
        group_cases = [c for c in cases if c.group == group]
        if not group_cases:
            continue
        async with mcp_session(GROUP_ENV[group]) as session:
            for case in group_cases:
                results.append(await _run_case(session, case))
    return results


def _report(results: list[Result]) -> bool:
    by_cat: dict[str, list[Result]] = defaultdict(list)
    for r in results:
        by_cat[r.case.category].append(r)

    print("\n=== MySQL MCP server evals ===\n")
    failures: list[Result] = []
    for category in sorted(by_cat):
        rs = by_cat[category]
        passed = sum(1 for r in rs if r.passed)
        print(f"{category:<16} {passed}/{len(rs)} passed")
        for r in rs:
            mark = "PASS" if r.passed else "FAIL"
            print(f"    [{mark}] {r.case.name}")
            if not r.passed:
                failures.append(r)

    total = len(results)
    total_pass = sum(1 for r in results if r.passed)
    print(f"\nTotal: {total_pass}/{total} passed")

    if failures:
        print("\nFailures:")
        for r in failures:
            print(f"  - {r.case.category} / {r.case.name}\n      {r.detail}")
    return not failures


async def _main_async() -> int:
    db = eval_db()
    print(f"Seeding eval database `{db}` ...")
    seed_database()
    try:
        results = await _run_all(build_cases(db))
    finally:
        teardown_database()
    ok = _report(results)
    return 0 if ok else 1


def main() -> None:
    load_local_env()
    if not mysql_available():
        print(
            "MySQL unavailable — skipping evals. "
            "Set MYSQL_HOST/PORT/USER/PASSWORD to a reachable MySQL to run them."
        )
        sys.exit(0)
    sys.exit(asyncio.run(_main_async()))


if __name__ == "__main__":
    main()
