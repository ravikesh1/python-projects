"""AI Knowledge Agent — a web-research knowledge system.

A shared local knowledge core (SQLite + FTS5) exposed two ways:

  - ``ai_knowledge_agent.mcp_server`` — an MCP server (stdio) so an MCP client
    such as Claude Desktop / Claude Code can search, ingest, and query it.
  - ``ai_knowledge_agent.cli`` — a standalone Claude-API agent (REPL) that drives
    the same knowledge core through tool use.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
