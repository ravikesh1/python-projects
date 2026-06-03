"""Bridge the existing MCP MySQL server into JARVIS's tool loop.

The MCP Python SDK is async, but JARVIS's conversation loop is synchronous. This
module runs an MCP stdio client on a dedicated background event loop and exposes
synchronous ``tool_specs()`` / ``handles()`` / ``call()`` methods, so MCP tools
plug into the same dispatch path as JARVIS's local tools.
"""

from __future__ import annotations

import asyncio
import os
import threading
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPToolProvider:
    """Launches an MCP stdio server as a subprocess and surfaces its tools."""

    def __init__(
        self,
        command: str,
        args: list[str],
        env: dict[str, str] | None = None,
        cwd: str | None = None,
    ) -> None:
        self._command = command
        self._args = args
        self._env = env
        self._cwd = cwd

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever, name="jarvis-mcp", daemon=True
        )
        self._stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None
        self._specs: list[dict[str, Any]] = []
        self._names: set[str] = set()
        self._started = False

    # -- lifecycle -------------------------------------------------------- #
    def start(self) -> "MCPToolProvider":
        """Spawn the server, initialise the session, and cache its tool list."""
        self._thread.start()
        self._submit(self._aopen())
        self._started = True
        return self

    def close(self) -> None:
        """Tear down the session, subprocess, and background loop."""
        if not self._started:
            return
        try:
            if self._stack is not None:
                self._submit(self._stack.aclose())
        except Exception:
            pass
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)
        self._started = False

    def __enter__(self) -> "MCPToolProvider":
        return self.start()

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- sync surface used by the assistant ------------------------------- #
    def tool_specs(self) -> list[dict[str, Any]]:
        return list(self._specs)

    def handles(self, name: str) -> bool:
        return name in self._names

    def call(self, name: str, arguments: dict[str, Any]) -> str:
        return self._submit(self._acall(name, arguments))

    # -- internals (run on the background loop) --------------------------- #
    def _submit(self, coro: Any) -> Any:
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()

    async def _aopen(self) -> None:
        self._stack = AsyncExitStack()
        params = StdioServerParameters(
            command=self._command, args=self._args, env=self._env, cwd=self._cwd
        )
        read, write = await self._stack.enter_async_context(stdio_client(params))
        self._session = await self._stack.enter_async_context(ClientSession(read, write))
        await self._session.initialize()

        result = await self._session.list_tools()
        for tool in result.tools:
            self._specs.append(
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.inputSchema,
                }
            )
            self._names.add(tool.name)

    async def _acall(self, name: str, arguments: dict[str, Any]) -> str:
        assert self._session is not None
        result = await self._session.call_tool(name, arguments)
        parts = [c.text for c in result.content if getattr(c, "type", None) == "text"]
        text = "\n".join(parts) if parts else "(no output)"
        if getattr(result, "isError", False):
            return f"Tool error: {text}"
        return text


def mysql_provider() -> MCPToolProvider:
    """Build a provider for this repo's MCP MySQL server (`uv run mcp-mysql-server`).

    The subprocess inherits the current environment (so MYSQL_* exported in the
    shell are passed through) and loads `.env` itself on startup.
    """
    return MCPToolProvider(
        command="uv",
        args=["run", "mcp-mysql-server"],
        env=dict(os.environ),
    )
