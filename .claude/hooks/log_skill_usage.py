#!/usr/bin/env python3
"""PostToolUse hook: log Skill tool invocations to a local JSONL file.

Reads the hook payload Claude Code passes on stdin, filters to the `Skill`
tool, and appends one JSON line per invocation to
.claude/skill-usage.log.jsonl (gitignored — local machine state only, not
part of the distributed plugin/skill).

This must never fail or block the tool call: any error here is swallowed.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

MAX_PROMPT_CHARS = 200
LOG_PATH = Path(__file__).resolve().parent.parent / "skill-usage.log.jsonl"


def last_user_text(transcript_path: str) -> str:
    """Best-effort: return the most recent user message's text from the
    session transcript JSONL (Claude Code passes its path in the payload)."""
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


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # malformed/missing payload: never block the tool call

    if payload.get("tool_name") != "Skill":
        return 0

    tool_input = payload.get("tool_input") or {}
    prompt = last_user_text(payload.get("transcript_path", ""))
    prompt_snippet = prompt[:MAX_PROMPT_CHARS] + ("…" if len(prompt) > MAX_PROMPT_CHARS else "")

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "skill": tool_input.get("skill", "unknown"),
        "args": tool_input.get("args"),
        "prompt_snippet": prompt_snippet,
        "session_id": payload.get("session_id"),
    }

    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass  # logging must never break the session

    return 0


if __name__ == "__main__":
    sys.exit(main())
