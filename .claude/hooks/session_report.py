#!/usr/bin/env python3
"""Read the session activity log written by log_session_activity.py.

Usage:
  python3 .claude/hooks/session_report.py                 # summary of recent sessions
  python3 .claude/hooks/session_report.py --limit 20      # more sessions
  python3 .claude/hooks/session_report.py --session <id>  # full timeline for one session
  python3 .claude/hooks/session_report.py --json          # machine-readable rollup
"""
import argparse
import json
from collections import OrderedDict
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "session-activity.jsonl"


def load_records(path: Path) -> list:
    if not path.exists():
        return []
    records = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # tolerate a partially written line
    return records


def group_by_session(records: list) -> "OrderedDict[str, list]":
    sessions: "OrderedDict[str, list]" = OrderedDict()
    for record in records:
        sessions.setdefault(record.get("session_id") or "unknown", []).append(record)
    return sessions


def session_rollup(session_id: str, records: list) -> dict:
    skills = [r for r in records if r.get("event") == "skill"]
    mcp_calls = [r for r in records if r.get("event") == "mcp_tool"]
    end = next((r for r in records if r.get("event") == "session_end"), None)
    start = next((r for r in records if r.get("event") == "session_start"), None)
    return {
        "session_id": session_id,
        "started_at": (start or {}).get("timestamp") or records[0].get("timestamp"),
        "ended_at": (end or {}).get("timestamp"),
        "cwd": records[0].get("cwd"),
        "skill_invocations": len(skills),
        "skills": sorted({r.get("skill") for r in skills if r.get("skill")}),
        "user_invoked_skills": sum(
            1 for r in skills if r.get("invocation_level") == "user_invoked"
        ),
        "model_invoked_skills": sum(
            1 for r in skills if r.get("invocation_level") == "model_invoked"
        ),
        "mcp_tool_calls": len(mcp_calls),
        "mcp_servers": sorted({r.get("server") for r in mcp_calls if r.get("server")}),
        "mcp_tools": sorted({r.get("tool") for r in mcp_calls if r.get("tool")}),
        "mcp_failures": sum(
            1 for r in mcp_calls if not (r.get("result") or {}).get("ok", True)
        ),
    }


def print_summary(rollups: list) -> None:
    if not rollups:
        print(f"No session activity logged yet ({LOG_PATH}).")
        return
    for roll in rollups:
        print(f"session {roll['session_id']}")
        print(f"  started : {roll['started_at']}")
        print(f"  ended   : {roll['ended_at'] or '(still open)'}")
        print(f"  cwd     : {roll['cwd']}")
        print(
            f"  skills  : {roll['skill_invocations']} invocation(s) "
            f"[user {roll['user_invoked_skills']} / model {roll['model_invoked_skills']}]"
            + (f" -> {', '.join(roll['skills'])}" if roll["skills"] else "")
        )
        print(
            f"  mcp     : {roll['mcp_tool_calls']} call(s), "
            f"{roll['mcp_failures']} failure(s)"
            + (f" -> {', '.join(roll['mcp_servers'])}" if roll["mcp_servers"] else "")
            + (f" [{', '.join(roll['mcp_tools'])}]" if roll["mcp_tools"] else "")
        )
        print()


def print_timeline(session_id: str, records: list) -> None:
    print(f"session {session_id} — {len(records)} record(s)\n")
    for record in records:
        stamp = record.get("timestamp", "")
        event = record.get("event", "?")
        if event == "skill":
            detail = (
                f"{record.get('skill')} ({record.get('invocation_level')}"
                f", #{record.get('invocation_number')})"
            )
            if record.get("args"):
                detail += f" args={record['args']}"
        elif event == "mcp_tool":
            result = record.get("result") or {}
            bits = [f"{record.get('server')}.{record.get('tool')}"]
            if record.get("database"):
                bits.append(f"db={record['database']}")
            if record.get("table"):
                bits.append(f"table={record['table']}")
            bits.append("ok" if result.get("ok", True) else "FAILED")
            if "row_count" in result:
                bits.append(f"rows={result['row_count']}")
            if result.get("truncated"):
                bits.append("truncated")
            detail = " ".join(bits)
            if record.get("query"):
                detail += f"\n      {record['query']}"
        elif event == "session_start":
            detail = f"source={record.get('source')}"
        elif event == "session_end":
            detail = f"reason={record.get('reason')} summary={json.dumps(record.get('summary', {}))}"
        else:
            detail = json.dumps(record, ensure_ascii=False)
        print(f"  {stamp}  {event:<14} {detail}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--session", help="show the full timeline for one session id")
    parser.add_argument("--limit", type=int, default=10, help="sessions to summarize (default 10)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument("--log", default=str(LOG_PATH), help="path to the activity log")
    args = parser.parse_args()

    sessions = group_by_session(load_records(Path(args.log)))

    if args.session:
        records = sessions.get(args.session)
        if not records:
            print(f"No records for session {args.session}")
            return 1
        if args.json:
            print(json.dumps(records, ensure_ascii=False, indent=2))
        else:
            print_timeline(args.session, records)
        return 0

    rollups = [session_rollup(sid, recs) for sid, recs in sessions.items()]
    rollups = rollups[-args.limit :]
    if args.json:
        print(json.dumps(rollups, ensure_ascii=False, indent=2))
    else:
        print_summary(rollups)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
