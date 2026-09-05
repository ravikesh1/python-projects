#!/usr/bin/env python3
"""Session activity logger for Claude Code.

Wired into settings.json on three hook events and appends one JSON line per
event to .claude/logs/session-activity.jsonl (gitignored — local machine
state, never part of the distributed plugin/skill):

  SessionStart  -> one `session_start` record per session
  PostToolUse   -> a `skill` record for every Skill invocation, and an
                   `mcp_tool` record for every MySQL MCP server tool call
  SessionEnd    -> one `session_end` record carrying a per-session rollup

This must never fail or block a tool call: any error here is swallowed and the
hook exits 0.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

MAX_PROMPT_CHARS = 200
MAX_QUERY_CHARS = 500
LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "session-activity.jsonl"

# mcp__<server>__<tool>; we care about servers whose name mentions mysql.
MCP_TOOL_RE = re.compile(r"^mcp__(?P<server>[^_].*?)__(?P<tool>.+)$")
MYSQL_SERVER_RE = re.compile(r"mysql", re.IGNORECASE)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def truncate(text: str, limit: int) -> str:
    text = text or ""
    return text[:limit] + ("…" if len(text) > limit else "")


def last_user_text(transcript_path: str) -> str:
    """Best-effort: the most recent user message's text from the session
    transcript JSONL (Claude Code passes its path in the payload)."""
    if not transcript_path:
        return ""
    try:
        with open(transcript_path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        return ""
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("type") == "user":
            content = entry.get("message", {}).get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = [
                    c.get("text", "")
                    for c in content
                    if isinstance(c, dict) and c.get("type") == "text"
                ]
                if parts:
                    return " ".join(parts)
    return ""


def read_session_records(session_id: str) -> list:
    """Every record already logged for this session (for counters/rollups)."""
    if not session_id or not LOG_PATH.exists():
        return []
    records = []
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("session_id") == session_id:
                    records.append(entry)
    except OSError:
        return []
    return records


def write_record(record: dict) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass  # logging must never break the session


def base_record(payload: dict, event: str) -> dict:
    return {
        "timestamp": now(),
        "event": event,
        "session_id": payload.get("session_id"),
        "cwd": payload.get("cwd") or os.getcwd(),
    }


def response_text(tool_response) -> str:
    """Flatten an MCP tool response into text for lightweight inspection."""
    if isinstance(tool_response, str):
        return tool_response
    if isinstance(tool_response, dict):
        content = tool_response.get("content", tool_response)
    else:
        content = tool_response
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    if isinstance(content, dict):
        return json.dumps(content, ensure_ascii=False)
    return str(content or "")


def summarize_result(tool_response) -> dict:
    """Best-effort row/truncation/error facts from a MySQL MCP result."""
    text = response_text(tool_response)
    summary = {"ok": True}
    if isinstance(tool_response, dict) and tool_response.get("isError"):
        summary["ok"] = False
    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        parsed = None
    if isinstance(parsed, dict):
        rows = parsed.get("rows")
        if isinstance(rows, list):
            summary["row_count"] = len(rows)
        elif isinstance(parsed.get("row_count"), int):
            summary["row_count"] = parsed["row_count"]
        if "truncated" in parsed:
            summary["truncated"] = bool(parsed["truncated"])
        if isinstance(parsed.get("affected_rows"), int):
            summary["affected_rows"] = parsed["affected_rows"]
        if parsed.get("error"):
            summary["ok"] = False
            summary["error"] = truncate(str(parsed["error"]), MAX_PROMPT_CHARS)
    elif isinstance(parsed, list):
        summary["row_count"] = len(parsed)
    if summary["ok"] and re.match(r"\s*(error|traceback)", text, re.IGNORECASE):
        summary["ok"] = False
        summary["error"] = truncate(text, MAX_PROMPT_CHARS)
    return summary


def handle_session_start(payload: dict) -> None:
    record = base_record(payload, "session_start")
    record.update(
        {
            "source": payload.get("source"),  # startup | resume | clear | compact
            "transcript_path": payload.get("transcript_path"),
        }
    )
    write_record(record)


def handle_skill(payload: dict) -> None:
    tool_input = payload.get("tool_input") or {}
    skill = tool_input.get("skill", "unknown")
    prompt = last_user_text(payload.get("transcript_path", ""))

    prior = read_session_records(payload.get("session_id"))
    invocation_number = sum(1 for r in prior if r.get("event") == "skill") + 1

    # "Level" of the invocation: did the user type /<skill>, or did the model
    # decide to load it?
    user_invoked = bool(re.match(rf"^\s*/{re.escape(skill)}\b", prompt or ""))

    record = base_record(payload, "skill")
    record.update(
        {
            "skill": skill,
            "args": tool_input.get("args"),
            "invocation_level": "user_invoked" if user_invoked else "model_invoked",
            "invocation_number": invocation_number,
            "prompt_snippet": truncate(prompt, MAX_PROMPT_CHARS),
        }
    )
    write_record(record)


def handle_mcp_tool(payload: dict, server: str, tool: str) -> None:
    tool_input = payload.get("tool_input") or {}
    query = tool_input.get("query") or tool_input.get("sql") or tool_input.get("statement")

    prior = read_session_records(payload.get("session_id"))
    call_number = sum(1 for r in prior if r.get("event") == "mcp_tool") + 1

    record = base_record(payload, "mcp_tool")
    record.update(
        {
            "server": server,
            "tool": tool,
            "kind": "mysql" if MYSQL_SERVER_RE.search(server) else "other",
            "call_number": call_number,
            "database": tool_input.get("database"),
            "table": tool_input.get("table"),
            "query": truncate(query, MAX_QUERY_CHARS) if query else None,
            "result": summarize_result(payload.get("tool_response")),
        }
    )
    write_record(record)


def handle_post_tool_use(payload: dict) -> None:
    tool_name = payload.get("tool_name") or ""
    if tool_name == "Skill":
        handle_skill(payload)
        return
    match = MCP_TOOL_RE.match(tool_name)
    if match and MYSQL_SERVER_RE.search(match.group("server")):
        handle_mcp_tool(payload, match.group("server"), match.group("tool"))


def handle_session_end(payload: dict) -> None:
    prior = read_session_records(payload.get("session_id"))
    skills = [r for r in prior if r.get("event") == "skill"]
    mcp_calls = [r for r in prior if r.get("event") == "mcp_tool"]
    started_at = next(
        (r.get("timestamp") for r in prior if r.get("event") == "session_start"), None
    )

    record = base_record(payload, "session_end")
    record.update(
        {
            "reason": payload.get("reason"),
            "started_at": started_at,
            "summary": {
                "skill_invocations": len(skills),
                "skills_used": sorted({r.get("skill") for r in skills if r.get("skill")}),
                "mcp_tool_calls": len(mcp_calls),
                "mcp_servers_used": sorted({r.get("server") for r in mcp_calls if r.get("server")}),
                "mcp_tools_used": sorted({r.get("tool") for r in mcp_calls if r.get("tool")}),
                "mcp_failures": sum(
                    1 for r in mcp_calls if not (r.get("result") or {}).get("ok", True)
                ),
            },
        }
    )
    write_record(record)


HANDLERS = {
    "SessionStart": handle_session_start,
    "PostToolUse": handle_post_tool_use,
    "SessionEnd": handle_session_end,
}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # malformed/missing payload: never block the tool call
    handler = HANDLERS.get(payload.get("hook_event_name"))
    if handler is None:
        # Fall back to tool-call handling so the hook still works if it is
        # wired up without an explicit event name.
        handler = handle_post_tool_use if payload.get("tool_name") else None
    if handler is None:
        return 0
    try:
        handler(payload)
    except Exception:
        pass  # logging must never break the session
    return 0


if __name__ == "__main__":
    sys.exit(main())
