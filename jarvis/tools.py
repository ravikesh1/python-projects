"""Tools JARVIS can call.

Three kinds:
  * Stateless local tools (date/time, calculator, system info) — pure functions
    executed on the host machine.
  * Personal tools (memory, tasks, notes) — operate on a persistent ``Store`` so
    JARVIS remembers across sessions, which is what makes it a personal
    assistant rather than a stateless chatbot.
  * Server-side tools (web search) — executed on Anthropic's infrastructure.
"""

from __future__ import annotations

import ast
import operator
import os
import platform
import shutil
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .store import Store

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
# Personal tools — operate on the persistent Store                            #
# --------------------------------------------------------------------------- #
# Each takes the Store as its first argument; the rest come from the model.
def _remember_fact(store: "Store", fact: str) -> str:
    return store.add_memory(fact)


def _forget_fact(store: "Store", query: str) -> str:
    return store.forget(query)


def _add_task(store: "Store", task: str, due: str | None = None) -> str:
    return store.add_task(task, due)


def _list_tasks(store: "Store", include_completed: bool = False) -> str:
    return store.list_tasks(include_completed)


def _complete_task(store: "Store", task_id: int | str) -> str:
    return store.complete_task(task_id)


def _add_note(store: "Store", note: str) -> str:
    return store.add_note(note)


def _list_notes(store: "Store") -> str:
    return store.list_notes()


def _delete_note(store: "Store", note_id: int | str) -> str:
    return store.delete_note(note_id)


# --------------------------------------------------------------------------- #
# Tool specifications                                                         #
# --------------------------------------------------------------------------- #
STATELESS_TOOLS: list[dict[str, Any]] = [
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

PERSONAL_TOOLS: list[dict[str, Any]] = [
    {
        "name": "remember_fact",
        "description": (
            "Save a durable fact about the user for future sessions — their "
            "name, preferences, important people/dates, ongoing projects, or "
            "anything they ask you to remember. Use this whenever the user "
            "shares something worth recalling later."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "fact": {
                    "type": "string",
                    "description": "The fact to remember, phrased clearly, e.g. "
                    "'The user's name is Ravi' or 'Prefers metric units'.",
                }
            },
            "required": ["fact"],
        },
    },
    {
        "name": "forget_fact",
        "description": "Remove remembered facts that match a phrase. Use when the "
        "user asks you to forget something or corrects outdated info.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Text to match against stored facts (case-insensitive).",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "add_task",
        "description": "Add a task or reminder to the user's to-do list. Use for "
        "anything they want to be reminded of or need to do.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "What needs doing."},
                "due": {
                    "type": "string",
                    "description": "Optional human-readable due time, e.g. 'tomorrow 9am'.",
                },
            },
            "required": ["task"],
        },
    },
    {
        "name": "list_tasks",
        "description": "List the user's tasks. Open tasks by default; set "
        "include_completed to also show finished ones.",
        "input_schema": {
            "type": "object",
            "properties": {
                "include_completed": {
                    "type": "boolean",
                    "description": "Include completed tasks too.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "complete_task",
        "description": "Mark a task done by its numeric id (from list_tasks).",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "integer", "description": "The task's id."}
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "add_note",
        "description": "Save a free-form note for the user (ideas, snippets, "
        "anything they want kept).",
        "input_schema": {
            "type": "object",
            "properties": {
                "note": {"type": "string", "description": "The note text."}
            },
            "required": ["note"],
        },
    },
    {
        "name": "list_notes",
        "description": "List all saved notes with their ids.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "delete_note",
        "description": "Delete a saved note by its numeric id (from list_notes).",
        "input_schema": {
            "type": "object",
            "properties": {
                "note_id": {"type": "integer", "description": "The note's id."}
            },
            "required": ["note_id"],
        },
    },
]

LOCAL_TOOLS: list[dict[str, Any]] = STATELESS_TOOLS + PERSONAL_TOOLS

# Anthropic-hosted web search. Executes server-side; no local handler needed.
SERVER_TOOLS: list[dict[str, Any]] = [
    {"type": "web_search_20260209", "name": "web_search"}
]

ALL_TOOLS: list[dict[str, Any]] = LOCAL_TOOLS + SERVER_TOOLS

# Stateless handlers: called with the model's input only.
_STATELESS_DISPATCH: dict[str, Callable[..., str]] = {
    "get_datetime": get_datetime,
    "calculate": calculate,
    "get_system_info": get_system_info,
}

# Personal handlers: called with the Store as their first argument.
_PERSONAL_DISPATCH: dict[str, Callable[..., str]] = {
    "remember_fact": _remember_fact,
    "forget_fact": _forget_fact,
    "add_task": _add_task,
    "list_tasks": _list_tasks,
    "complete_task": _complete_task,
    "add_note": _add_note,
    "list_notes": _list_notes,
    "delete_note": _delete_note,
}


def execute_local_tool(
    name: str, tool_input: dict[str, Any], store: "Store | None" = None
) -> str:
    """Run a local tool by name and return its textual result."""
    if name in _STATELESS_DISPATCH:
        return _STATELESS_DISPATCH[name](**tool_input)
    if name in _PERSONAL_DISPATCH:
        if store is None:
            return "Personal storage is unavailable in this session."
        return _PERSONAL_DISPATCH[name](store, **tool_input)
    return f"Unknown tool: {name}"
