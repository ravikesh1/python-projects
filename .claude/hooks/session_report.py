#!/usr/bin/env python3
"""Read the session activity log written by log_session_activity.py.

Usage:
  python3 .claude/hooks/session_report.py                 # summary of recent sessions
  python3 .claude/hooks/session_report.py --limit 20      # more sessions
  python3 .claude/hooks/session_report.py --session <id>  # full timeline for one session
  python3 .claude/hooks/session_report.py --json          # machine-readable rollup
  python3 .claude/hooks/session_report.py --feedback      # only feedback / bug reports
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
    feedback = [r for r in records if r.get("event") == "feedback"]
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
        "feedback_reports": len(feedback),
        "feedback_ids": [r.get("report_id") for r in feedback if r.get("report_id")],
        "feedback_severities": sorted({r.get("severity") for r in feedback if r.get("severity")}),
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
        if roll["feedback_reports"]:
            print(
                f"  feedback: {roll['feedback_reports']} report(s)"
                + (f" [{', '.join(roll['feedback_severities'])}]" if roll["feedback_severities"] else "")
                + (f" -> {', '.join(roll['feedback_ids'])}" if roll["feedback_ids"] else "")
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
        elif event == "feedback":
            result = record.get("result") or {}
            bits = [f"{record.get('server')}.{record.get('tool')}"]
            if record.get("severity"):
                bits.append(f"severity={record['severity']}")
            if record.get("category"):
                bits.append(f"category={record['category']}")
            if record.get("report_id"):
                bits.append(f"id={record['report_id']}")
            bits.append("ok" if result.get("ok", True) else "FAILED")
            detail = " ".join(bits)
            if record.get("description"):
                detail += f"\n      {record['description']}"
            if record.get("context"):
                detail += f"\n      context: {record['context']}"
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
    parser.add_argument(
        "--feedback", action="store_true", help="list only feedback / bug reports"
    )
    parser.add_argument("--log", default=str(LOG_PATH), help="path to the activity log")
    args = parser.parse_args()

    records = load_records(Path(args.log))

    if args.feedback:
        reports = [r for r in records if r.get("event") == "feedback"]
        if args.session:
            reports = [r for r in reports if r.get("session_id") == args.session]
        if args.json:
            print(json.dumps(reports, ensure_ascii=False, indent=2))
        elif not reports:
            print("No feedback / bug reports logged yet.")
        else:
            for report in reports:
                print(
                    f"{report.get('timestamp')}  {report.get('report_id') or '(no id)'}  "
                    f"severity={report.get('severity')} category={report.get('category')}  "
                    f"session={report.get('session_id')}"
                )
                if report.get("description"):
                    print(f"    {report['description']}")
                if report.get("context"):
                    print(f"    context: {report['context']}")
                print()
        return 0

    sessions = group_by_session(records)

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
