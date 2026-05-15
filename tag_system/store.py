"""Tiny JSON-backed store of tagged documents."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

from tag_system.tagger import Tags


def _store_path() -> Path:
    return Path(os.getenv("TAG_STORE_PATH", ".tag_store.json"))


def _load() -> dict[str, dict]:
    path = _store_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text() or "{}")


def _save(items: dict[str, dict]) -> None:
    _store_path().write_text(json.dumps(items, indent=2, ensure_ascii=False))


def save_item(text: str, tags: Tags) -> str:
    items = _load()
    item_id = uuid.uuid4().hex[:8]
    items[item_id] = {"text": text, "tags": tags.model_dump()}
    _save(items)
    return item_id


def list_items() -> dict[str, dict]:
    return _load()


def search_by_topic(topic: str) -> dict[str, dict]:
    topic = topic.lower().strip()
    return {
        item_id: item
        for item_id, item in _load().items()
        if any(topic in t.lower() for t in item["tags"].get("topics", []))
    }
