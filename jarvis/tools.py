"""Tools JARVIS can call.

Two kinds:
  * Local tools (date/time, calculator, system info) — executed here, on the
    machine JARVIS is running on. Defined as JSON-schema tool specs plus a
    dispatcher.
  * Server-side tools (web search) — executed on Anthropic's infrastructure;
    we only declare them and let the model drive.
"""

from __future__ import annotations

import ast
import operator
import os
import platform
import shutil
from datetime import datetime
from typing import Any, Callable

try:  # Python 3.9+ stdlib; present on 3.10+ which this project targets.
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - defensive only
    ZoneInfo = None  # type: ignore[assignment]


# --------------------------------------------------------------------------- #
# Local tool: current date and time                                           #
# --------------------------------------------------------------------------- #
def get_datetime(timezone: str | None = None) -> str:
    """Return the current date and time, optionally in a named timezone."""
    if timezone and ZoneInfo is not None:
        try:
            now = datetime.now(ZoneInfo(timezone))
        except Exception:
            return (
                f"I couldn't recognise the timezone {timezone!r}. "
                "Try an IANA name like 'America/New_York' or 'Europe/London'."
            )
    else:
        now = datetime.now().astimezone()

    return now.strftime("%A, %d %B %Y at %I:%M:%S %p %Z").strip()


# --------------------------------------------------------------------------- #
# Local tool: safe arithmetic calculator                                      #
# --------------------------------------------------------------------------- #
_BIN_OPS: dict[type, Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS: dict[type, Callable[[Any], Any]] = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node: ast.AST) -> float | int:
    if isinstance(node, ast.Constant):  # numeric literal
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ValueError("only numbers are allowed")
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("unsupported expression")


def calculate(expression: str) -> str:
    """Evaluate a basic arithmetic expression safely (no names, no calls)."""
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree.body)
    except ZeroDivisionError:
        return "That would be a division by zero, sir — mathematically off the table."
    except Exception:
        return (
            f"I couldn't evaluate {expression!r}. I handle + - * / // % and ** "
            "on plain numbers and parentheses."
        )
    return f"{expression} = {result}"


# --------------------------------------------------------------------------- #
# Local tool: system diagnostics                                              #
# --------------------------------------------------------------------------- #
def _read_linux_memory() -> str | None:
    try:
        with open("/proc/meminfo", encoding="utf-8") as fh:
            info = {}
            for line in fh:
                key, _, rest = line.partition(":")
                info[key.strip()] = rest.strip()
        total_kb = int(info["MemTotal"].split()[0])
        avail_kb = int(info.get("MemAvailable", "0").split()[0])
        return (
            f"{total_kb / 1024 / 1024:.1f} GiB total, "
            f"{avail_kb / 1024 / 1024:.1f} GiB available"
        )
    except Exception:
        return None


def get_system_info() -> str:
    """Report basic diagnostics about the host machine."""
    parts = [
        f"OS: {platform.system()} {platform.release()} ({platform.machine()})",
        f"Python: {platform.python_version()}",
        f"CPU cores: {os.cpu_count()}",
    ]

    memory = _read_linux_memory()
    if memory:
        parts.append(f"Memory: {memory}")

    try:
        usage = shutil.disk_usage("/")
        parts.append(
            f"Disk (/): {usage.total / 1024**3:.0f} GiB total, "
            f"{usage.free / 1024**3:.0f} GiB free"
        )
    except Exception:
        pass

    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# Tool specifications                                                         #
# --------------------------------------------------------------------------- #
LOCAL_TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_datetime",
        "description": (
            "Get the current local date and time. Call this whenever the user "
            "asks what time or day it is, or when you need the current moment to "
            "answer accurately. Optionally accepts an IANA timezone name."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": (
                        "Optional IANA timezone, e.g. 'Europe/London' or "
                        "'America/New_York'. Omit for the machine's local time."
                    ),
                }
            },
            "required": [],
        },
    },
    {
        "name": "calculate",
        "description": (
            "Evaluate a basic arithmetic expression. Call this for any numeric "
            "calculation rather than computing it yourself. Supports + - * / // "
            "% ** and parentheses on plain numbers."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The arithmetic expression, e.g. '(3 + 4) * 2 ** 5'.",
                }
            },
            "required": ["expression"],
        },
    },
    {
        "name": "get_system_info",
        "description": (
            "Report diagnostics about the machine JARVIS is running on: OS, "
            "Python version, CPU core count, memory, and disk. Call this when "
            "the user asks about the system, hardware, or resources."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]

# Anthropic-hosted web search. Executes server-side; no local handler needed.
SERVER_TOOLS: list[dict[str, Any]] = [
    {"type": "web_search_20260209", "name": "web_search"}
]

ALL_TOOLS: list[dict[str, Any]] = LOCAL_TOOLS + SERVER_TOOLS

_DISPATCH: dict[str, Callable[..., str]] = {
    "get_datetime": get_datetime,
    "calculate": calculate,
    "get_system_info": get_system_info,
}


def execute_local_tool(name: str, tool_input: dict[str, Any]) -> str:
    """Run a local tool by name and return its textual result."""
    handler = _DISPATCH.get(name)
    if handler is None:
        return f"Unknown tool: {name}"
    return handler(**tool_input)
