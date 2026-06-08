"""Standalone Claude-powered research agent (REPL).

This is the "Batcomputer" you talk to directly in a terminal. It drives the same
knowledge core as the MCP server through tool use: it searches the web, ingests
pages into a local knowledge base, and reasons over what it has learned to help
you build things. Requires ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import anthropic
from dotenv import load_dotenv

from .config import Config
from .ingest import FetchError, Knowledge, SearchError

logger = logging.getLogger("ai-knowledge-agent")

SYSTEM_PROMPT = """\
You are the Batcomputer: a research and creation assistant with a persistent,
local knowledge base. Your job is to help the user create amazing things by
gathering high-quality information and reasoning carefully over it.

How to work:
- When a question needs current or external information, use web_search to find
  sources, then ingest_url / ingest_search to store the useful ones in the
  knowledge base before answering.
- Prefer search_knowledge first — reuse what you've already ingested instead of
  re-fetching.
- Ground your answers in stored documents and cite them by their id and url.
- Be concrete and practical: when the user wants to build something, turn the
  research into clear, actionable steps.
- If sources conflict or are thin, say so plainly.
"""

TOOLS: list[dict[str, Any]] = [
    {
        "name": "web_search",
        "description": "Search the web and return title/url/snippet. Does not store anything.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "ingest_url",
        "description": "Fetch a URL, extract its text, and store it in the knowledge base.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    },
    {
        "name": "ingest_search",
        "description": "Search the web and ingest the top results into the knowledge base.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "num_results": {"type": "integer"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_knowledge",
        "description": "Keyword/full-text search across documents already in the knowledge base.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_document",
        "description": "Retrieve a stored document's full text and metadata by id.",
        "input_schema": {
            "type": "object",
            "properties": {"id": {"type": "integer"}},
            "required": ["id"],
        },
    },
    {
        "name": "list_documents",
        "description": "List recently ingested documents.",
        "input_schema": {
            "type": "object",
            "properties": {"limit": {"type": "integer"}},
        },
    },
    {
        "name": "knowledge_stats",
        "description": "Report knowledge-base statistics.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def execute_tool(knowledge: Knowledge, name: str, args: dict[str, Any]) -> str:
    if name == "web_search":
        return json.dumps(knowledge.search_web(args["query"], args.get("max_results")))
    if name == "ingest_url":
        return json.dumps(knowledge.ingest_url(args["url"]))
    if name == "ingest_search":
        return json.dumps(knowledge.ingest_search(args["query"], args.get("num_results")))
    if name == "search_knowledge":
        return json.dumps(knowledge.search_knowledge(args["query"], args.get("limit")))
    if name == "get_document":
        doc = knowledge.get_document(int(args["id"]))
        return json.dumps(doc) if doc else f"No document with id {args['id']}"
    if name == "list_documents":
        return json.dumps(knowledge.list_documents(int(args.get("limit", 20))))
    if name == "knowledge_stats":
        return json.dumps(knowledge.stats())
    return f"Unknown tool: {name}"


def _run_turn(
    client: anthropic.Anthropic,
    knowledge: Knowledge,
    model: str,
    messages: list[dict[str, Any]],
) -> None:
    """Run one user turn to completion, executing tools until Claude is done."""
    while True:
        response = client.messages.create(
            model=model,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"\nbatcomputer> {block.text.strip()}\n")

        if response.stop_reason != "tool_use":
            return

        tool_results: list[dict[str, Any]] = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f"  [tool] {block.name}({json.dumps(block.input)})")
            try:
                result = execute_tool(knowledge, block.name, dict(block.input))
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result}
                )
            except (FetchError, SearchError, ValueError, KeyError) as exc:
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Error: {exc}",
                        "is_error": True,
                    }
                )
        messages.append({"role": "user", "content": tool_results})


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "WARNING"))

    if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")):
        print(
            "ANTHROPIC_API_KEY is not set. Export it (or add it to .env) to use the "
            "CLI agent. The MCP server (ai-knowledge-mcp) does not require it."
        )
        raise SystemExit(1)

    config = Config.from_env()
    knowledge = Knowledge(config)
    client = anthropic.Anthropic()
    messages: list[dict[str, Any]] = []

    print("Batcomputer online. Ask a research question, or type 'exit' to quit.")
    print(f"Knowledge base: {config.db_path}\n")

    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", ":q"}:
            break

        messages.append({"role": "user", "content": user_input})
        try:
            _run_turn(client, knowledge, config.model, messages)
        except anthropic.APIError as exc:
            print(f"\n[API error] {exc}\n")


if __name__ == "__main__":
    main()
