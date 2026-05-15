"""LangGraph ReAct agent that orchestrates tagging + storage tools."""

from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from tag_system import store
from tag_system.tagger import Tagger


@tool
def tag_text(text: str) -> dict:
    """Extract structured tags (sentiment, language, aggressiveness, topics) from text."""
    return Tagger().tag(text).model_dump()


@tool
def save_tagged(text: str) -> str:
    """Tag the given text and persist it to the local store. Returns the item id."""
    tags = Tagger().tag(text)
    return store.save_item(text, tags)


@tool
def search_topic(topic: str) -> str:
    """Find stored items whose topic tags contain the given substring (case-insensitive)."""
    hits = store.search_by_topic(topic)
    return json.dumps(hits, ensure_ascii=False)


@tool
def list_all() -> str:
    """Return every stored item as JSON."""
    return json.dumps(store.list_items(), ensure_ascii=False)


TOOLS = [tag_text, save_tagged, search_topic, list_all]


def build_agent(model: str | None = None):
    """Build a ReAct agent wired to the tagging tools."""
    model = model or os.getenv("TAG_MODEL", "claude-sonnet-4-5-20250929")
    llm = ChatAnthropic(model=model, temperature=0)
    return create_react_agent(llm, TOOLS)
