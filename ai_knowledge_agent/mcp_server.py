"""MCP server exposing the knowledge core over stdio.

Tools:
  - web_search       Search the web (DuckDuckGo); does not store anything.
  - ingest_url       Fetch a URL, extract text, store it in the knowledge base.
  - ingest_search    Search the web and ingest the top results.
  - search_knowledge Keyword/full-text search across stored documents.
  - get_document     Retrieve a stored document's full text by id.
  - list_documents   List recently ingested documents.
  - delete_document  Remove a document by id.
  - knowledge_stats  Report knowledge-base statistics.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .config import Config
from .ingest import FetchError, Knowledge, SearchError

logger = logging.getLogger("ai-knowledge-mcp")


def build_server(knowledge: Knowledge) -> Server:
    server: Server = Server("ai-knowledge-agent")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="web_search",
                description=(
                    "Search the web (DuckDuckGo) and return title/url/snippet for "
                    "each result. Does not store anything — use ingest_url or "
                    "ingest_search to add pages to the knowledge base."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query."},
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results.",
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="ingest_url",
                description="Fetch a URL, extract its readable text, and store it in the knowledge base.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The URL to ingest."},
                    },
                    "required": ["url"],
                },
            ),
            Tool(
                name="ingest_search",
                description="Search the web and ingest the top results into the knowledge base.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query."},
                        "num_results": {
                            "type": "integer",
                            "description": "How many top results to ingest.",
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="search_knowledge",
                description="Keyword/full-text search across documents already stored in the knowledge base.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query."},
                        "limit": {"type": "integer", "description": "Maximum number of hits."},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="get_document",
                description="Retrieve a stored document's full text and metadata by its id.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "description": "Document id."},
                    },
                    "required": ["id"],
                },
            ),
            Tool(
                name="list_documents",
                description="List recently ingested documents (id, url, title, source, size).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Maximum number of documents."},
                    },
                },
            ),
            Tool(
                name="delete_document",
                description="Delete a document from the knowledge base by its id.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "description": "Document id."},
                    },
                    "required": ["id"],
                },
            ),
            Tool(
                name="knowledge_stats",
                description="Report knowledge-base statistics (document count, total size, backend).",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        try:
            payload = await asyncio.to_thread(_dispatch, name, arguments or {})
            text = json.dumps(payload, indent=2)
        except (FetchError, SearchError) as exc:
            text = f"Error: {exc}"
        except ValueError as exc:
            text = f"Invalid request: {exc}"
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected error handling tool %s", name)
            text = f"Unexpected error: {exc}"
        return [TextContent(type="text", text=text)]

    def _dispatch(name: str, args: dict[str, Any]) -> Any:
        if name == "web_search":
            return knowledge.search_web(_require_str(args, "query"), args.get("max_results"))
        if name == "ingest_url":
            return knowledge.ingest_url(_require_str(args, "url"))
        if name == "ingest_search":
            return knowledge.ingest_search(_require_str(args, "query"), args.get("num_results"))
        if name == "search_knowledge":
            return knowledge.search_knowledge(_require_str(args, "query"), args.get("limit"))
        if name == "get_document":
            doc = knowledge.get_document(_require_int(args, "id"))
            if doc is None:
                raise ValueError(f"No document with id {args.get('id')}")
            return doc
        if name == "list_documents":
            return knowledge.list_documents(int(args.get("limit", 50)))
        if name == "delete_document":
            ok = knowledge.delete_document(_require_int(args, "id"))
            return {"deleted": ok, "id": args.get("id")}
        if name == "knowledge_stats":
            return knowledge.stats()
        raise ValueError(f"Unknown tool: {name}")

    return server


def _require_str(args: dict[str, Any], key: str) -> str:
    value = args.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"'{key}' is required and must be a non-empty string.")
    return value


def _require_int(args: dict[str, Any], key: str) -> int:
    value = args.get(key)
    if value is None:
        raise ValueError(f"'{key}' is required.")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"'{key}' must be an integer.") from exc


async def _run() -> None:
    load_dotenv()
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    knowledge = Knowledge(Config.from_env())
    server = build_server(knowledge)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
