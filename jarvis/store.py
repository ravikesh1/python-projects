"""Persistent local storage for JARVIS — what makes it feel personal.

A small JSON-backed store under ``~/.jarvis/`` (override with ``JARVIS_HOME``)
holding three things that survive across sessions:

  * memories — durable facts about the user (name, preferences, context)
  * tasks    — a to-do / reminder list
  * notes    — free-form jottings

Writes are atomic (temp file + ``os.replace``) so a crash can't corrupt data.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


def _default_home() -> Path:
    return Path(os.getenv("JARVIS_HOME", str(Path.home() / ".jarvis")))


class Store:
    """A tiny persistent store for memories, tasks, and notes."""

    def __init__(self, home: Path | None = None) -> None:
        self.home = home or _default_home()
        self.path = self.home / "data.json"
        self._data: dict[str, Any] = {
            "seq": 1,
            "memories": [],
            "tasks": [],
            "notes": [],
        }
        self.load()

    # -- persistence ------------------------------------------------------ #
    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self._data.update(loaded)
        except (json.JSONDecodeError, OSError):
            # Corrupt or unreadable: start fresh rather than crash.
            pass

    def save(self) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.home, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2)
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def _next_id(self) -> int:
        seq = int(self._data.get("seq", 1))
        self._data["seq"] = seq + 1
        return seq

    @staticmethod
    def _now() -> str:
        return datetime.now().astimezone().isoformat(timespec="seconds")

    # -- memories --------------------------------------------------------- #
    def add_memory(self, fact: str) -> str:
        fact = fact.strip()
        if not fact:
            return "Nothing to remember — the fact was empty."
        self._data["memories"].append({"fact": fact, "added": self._now()})
        self.save()
        return f"Noted and stored: {fact}"

    def forget(self, query: str) -> str:
        query = query.strip().lower()
        before = self._data["memories"]
        kept = [m for m in before if query not in m["fact"].lower()]
        removed = len(before) - len(kept)
        if not removed:
            return f"I have nothing on record matching {query!r}."
        self._data["memories"] = kept
        self.save()
        return f"Forgotten {removed} item(s) matching {query!r}."

    def memories(self) -> list[str]:
        return [m["fact"] for m in self._data["memories"]]

    # -- tasks ------------------------------------------------------------ #
    def add_task(self, task: str, due: str | None = None) -> str:
        task = task.strip()
        if not task:
            return "Nothing to add — the task was empty."
        task_id = self._next_id()
        self._data["tasks"].append(
            {"id": task_id, "task": task, "due": due, "done": False, "added": self._now()}
        )
        self.save()
        suffix = f" (due {due})" if due else ""
        return f"Added task [{task_id}]: {task}{suffix}"

    def list_tasks(self, include_completed: bool = False) -> str:
        tasks = self._data["tasks"]
        if not include_completed:
            tasks = [t for t in tasks if not t["done"]]
        if not tasks:
            return "No tasks on the list." if include_completed else "No open tasks."
        lines = []
        for t in tasks:
            mark = "x" if t["done"] else " "
            due = f" (due {t['due']})" if t.get("due") else ""
            lines.append(f"[{mark}] {t['id']}: {t['task']}{due}")
        return "\n".join(lines)

    def complete_task(self, task_id: int | str) -> str:
        try:
            tid = int(task_id)
        except (TypeError, ValueError):
            return f"{task_id!r} isn't a valid task id."
        for t in self._data["tasks"]:
            if t["id"] == tid:
                if t["done"]:
                    return f"Task [{tid}] was already done."
                t["done"] = True
                self.save()
                return f"Marked task [{tid}] done: {t['task']}"
        return f"No task with id {tid}."

    # -- notes ------------------------------------------------------------ #
    def add_note(self, note: str) -> str:
        note = note.strip()
        if not note:
            return "Nothing to note — the note was empty."
        note_id = self._next_id()
        self._data["notes"].append({"id": note_id, "note": note, "added": self._now()})
        self.save()
        return f"Saved note [{note_id}]."

    def list_notes(self) -> str:
        notes = self._data["notes"]
        if not notes:
            return "No notes saved."
        return "\n".join(f"{n['id']}: {n['note']}" for n in notes)

    def delete_note(self, note_id: int | str) -> str:
        try:
            nid = int(note_id)
        except (TypeError, ValueError):
            return f"{note_id!r} isn't a valid note id."
        before = self._data["notes"]
        kept = [n for n in before if n["id"] != nid]
        if len(kept) == len(before):
            return f"No note with id {nid}."
        self._data["notes"] = kept
        self.save()
        return f"Deleted note [{nid}]."

    # -- session startup snapshot ---------------------------------------- #
    def context_snapshot(self) -> str | None:
        """A read-only summary injected at session start for continuity.

        Lets JARVIS greet the user already knowing their facts and open tasks,
        without spending a tool call. Returns None if there's nothing to show.
        """
        sections: list[str] = []
        facts = self.memories()
        if facts:
            sections.append(
                "Known facts about the user:\n"
                + "\n".join(f"- {f}" for f in facts)
            )
        open_tasks = [t for t in self._data["tasks"] if not t["done"]]
        if open_tasks:
            lines = [
                f"- [{t['id']}] {t['task']}" + (f" (due {t['due']})" if t.get("due") else "")
                for t in open_tasks
            ]
            sections.append("Open tasks:\n" + "\n".join(lines))
        if not sections:
            return None
        return (
            "Context loaded at the start of this session (use it for continuity; "
            "call the memory/task tools to make any changes):\n\n"
            + "\n\n".join(sections)
        )
