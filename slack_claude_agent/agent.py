"""Claude conversation logic for the Slack agent."""

import logging
import os

import anthropic

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """\
You are a helpful AI assistant that lives in Slack. People talk to you by \
sending you direct messages or by @mentioning you in channels.

Formatting rules — Slack uses mrkdwn, not standard Markdown:
- *bold* with single asterisks, _italic_ with underscores, ~strikethrough~ with tildes
- `inline code` and ```code blocks``` work as usual (no language tags)
- Bullet lists with "•" or "-"; there are no headers, so bold a short line instead
- Links as <https://example.com|link text>

Keep responses concise and conversational — this is chat, not a document. \
Use short paragraphs. Only go long when the question genuinely needs it.\
"""


class ClaudeAgent:
    """Thin wrapper around the Anthropic SDK for multi-turn Slack chats."""

    def __init__(self) -> None:
        # Reads ANTHROPIC_API_KEY from the environment.
        self.client = anthropic.Anthropic()
        self.model = os.environ.get("CLAUDE_MODEL", DEFAULT_MODEL)
        self.max_tokens = int(os.environ.get("CLAUDE_MAX_TOKENS", "16000"))

    def reply(self, messages: list[dict]) -> str:
        """Send the conversation to Claude and return the assistant's text.

        ``messages`` is a list of ``{"role": "user"|"assistant", "content": str}``
        dicts ordered oldest-first, ending with the message to respond to.
        """
        with self.client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            thinking={"type": "adaptive"},
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=messages,
        ) as stream:
            final = stream.get_final_message()

        text = "".join(b.text for b in final.content if b.type == "text")
        if final.stop_reason == "max_tokens":
            text += "\n\n_(response truncated — hit the output token limit)_"
        return text
