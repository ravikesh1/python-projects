"""The JARVIS conversation engine: a streaming, tool-using loop over the Claude API."""

from __future__ import annotations

import os
from typing import Any, Callable

import anthropic

from .persona import JARVIS_PERSONA
from .tools import ALL_TOOLS, execute_local_tool

DEFAULT_MODEL = "claude-opus-4-8"
DEFAULT_EFFORT = "low"  # snappy by default; this is a conversational assistant
DEFAULT_MAX_TOKENS = 4096


class Jarvis:
    """A stateful, multi-turn JARVIS session.

    The Anthropic API is stateless, so the full conversation history is resent
    on every turn — kept in ``self.messages``.
    """

    def __init__(
        self,
        client: anthropic.Anthropic | None = None,
        model: str = DEFAULT_MODEL,
        effort: str = DEFAULT_EFFORT,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        # The client resolves ANTHROPIC_API_KEY from the environment by default.
        self.client = client or anthropic.Anthropic()
        self.model = model
        self.effort = effort
        self.max_tokens = max_tokens
        self.messages: list[dict[str, Any]] = []

        # System prompt is frozen (no volatile content), so cache it. The
        # breakpoint is harmless on short prompts and pays off as it grows.
        self._system = [
            {
                "type": "text",
                "text": JARVIS_PERSONA,
                "cache_control": {"type": "ephemeral"},
            }
        ]

    def ask(
        self,
        user_text: str,
        on_text: Callable[[str], None] | None = None,
        on_tool: Callable[[str], None] | None = None,
    ) -> str:
        """Send a user message and run the loop until JARVIS gives a final answer.

        ``on_text`` receives streamed text chunks (for live terminal output).
        ``on_tool`` receives a short note when a local tool is invoked.
        Returns the complete final reply text.
        """
        self.messages.append({"role": "user", "content": user_text})
        reply_parts: list[str] = []

        while True:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self._system,
                messages=self.messages,
                tools=ALL_TOOLS,
                thinking={"type": "adaptive"},
                output_config={"effort": self.effort},
            ) as stream:
                for chunk in stream.text_stream:
                    reply_parts.append(chunk)
                    if on_text is not None:
                        on_text(chunk)
                response = stream.get_final_message()

            # Preserve the full content (incl. tool_use / thinking blocks).
            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "tool_use":
                tool_results = self._run_local_tools(response.content, on_tool)
                if tool_results:
                    self.messages.append({"role": "user", "content": tool_results})
                continue

            if response.stop_reason == "pause_turn":
                # A server-side tool (web search) hit its iteration limit.
                # Re-send as-is; the server resumes automatically.
                continue

            break

        return "".join(reply_parts).strip()

    def _run_local_tools(
        self,
        content: list[Any],
        on_tool: Callable[[str], None] | None,
    ) -> list[dict[str, Any]]:
        """Execute every local tool_use block; return tool_result blocks."""
        results: list[dict[str, Any]] = []
        for block in content:
            if getattr(block, "type", None) != "tool_use":
                continue
            if on_tool is not None:
                on_tool(block.name)
            try:
                output = execute_local_tool(block.name, dict(block.input))
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": output,
                    }
                )
            except Exception as exc:  # surface failures back to the model
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Tool error: {exc}",
                        "is_error": True,
                    }
                )
        return results


def make_default_client() -> anthropic.Anthropic:
    """Build a client, with a friendly error if the API key is missing."""
    if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")):
        raise RuntimeError(
            "No Anthropic credentials found. Set ANTHROPIC_API_KEY in your "
            "environment or in a .env file (see .env.example)."
        )
    return anthropic.Anthropic()
