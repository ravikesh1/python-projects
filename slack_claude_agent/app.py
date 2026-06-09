"""Slack entrypoint: Bolt app running in Socket Mode."""

import logging
import os
import re

import anthropic
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from slack_claude_agent.agent import ClaudeAgent

logger = logging.getLogger(__name__)

# Slack rejects messages over 40k chars and renders very long ones poorly.
MAX_SLACK_CHUNK = 3900
HISTORY_LIMIT = 40

MENTION_RE = re.compile(r"<@[A-Z0-9]+>")


def _strip_mentions(text: str) -> str:
    return MENTION_RE.sub("", text or "").strip()


def _chunk(text: str, size: int = MAX_SLACK_CHUNK) -> list[str]:
    """Split text into Slack-sized chunks, preferring newline boundaries."""
    chunks = []
    while len(text) > size:
        cut = text.rfind("\n", 0, size)
        if cut <= 0:
            cut = size
        chunks.append(text[:cut])
        text = text[cut:].lstrip("\n")
    if text:
        chunks.append(text)
    return chunks or [""]


def _build_conversation(slack_messages: list[dict], bot_user_id: str) -> list[dict]:
    """Convert Slack messages (oldest-first) into Claude API messages.

    The bot's own messages become assistant turns; everything else becomes
    user turns. Consecutive same-role messages are allowed by the API.
    """
    conversation = []
    for msg in slack_messages:
        if msg.get("subtype"):  # joins, edits, bot attachments, etc.
            continue
        text = _strip_mentions(msg.get("text", ""))
        if not text:
            continue
        role = "assistant" if msg.get("user") == bot_user_id else "user"
        conversation.append({"role": role, "content": text})
    # The API requires the first message to be a user turn.
    while conversation and conversation[0]["role"] != "user":
        conversation.pop(0)
    return conversation


class SlackClaudeBot:
    def __init__(self) -> None:
        self.app = App(token=os.environ["SLACK_BOT_TOKEN"])
        self.agent = ClaudeAgent()
        self.bot_user_id = self.app.client.auth_test()["user_id"]

        self.app.event("app_mention")(self.handle_mention)
        self.app.event("message")(self.handle_message)

    # -- event handlers -------------------------------------------------

    def handle_mention(self, event: dict, say, client) -> None:
        """@mention in a channel: reply in the message's thread."""
        thread_ts = event.get("thread_ts") or event["ts"]
        self._respond(event, say, client, thread_ts=thread_ts, in_thread=True)

    def handle_message(self, event: dict, say, client) -> None:
        """Direct message to the bot."""
        if event.get("channel_type") != "im":
            return  # channel messages are handled via app_mention
        if event.get("subtype") or event.get("bot_id"):
            return
        if event.get("user") == self.bot_user_id:
            return
        self._respond(event, say, client, thread_ts=event.get("thread_ts"), in_thread=False)

    # -- core ------------------------------------------------------------

    def _respond(self, event: dict, say, client, thread_ts: str | None, in_thread: bool) -> None:
        channel = event["channel"]
        try:
            client.reactions_add(channel=channel, timestamp=event["ts"], name="eyes")
        except Exception:
            pass  # cosmetic only

        try:
            history = self._fetch_context(client, channel, thread_ts, in_thread)
            conversation = _build_conversation(history, self.bot_user_id)
            if not conversation:
                conversation = [{"role": "user", "content": _strip_mentions(event.get("text", "")) or "Hello"}]
            reply = self.agent.reply(conversation)
        except anthropic.AuthenticationError:
            reply = ":warning: My Anthropic API key is missing or invalid. Check `ANTHROPIC_API_KEY`."
        except anthropic.RateLimitError:
            reply = ":hourglass: I'm being rate-limited right now — try again in a minute."
        except anthropic.APIStatusError as e:
            logger.exception("Claude API error")
            reply = f":warning: Claude API error ({e.status_code}). Try again shortly."
        except Exception:
            logger.exception("Unexpected error while generating a reply")
            reply = ":warning: Something went wrong on my end. Try again shortly."

        for chunk in _chunk(reply):
            say(text=chunk, thread_ts=thread_ts, channel=channel)

    def _fetch_context(self, client, channel: str, thread_ts: str | None, in_thread: bool) -> list[dict]:
        """Pull recent Slack messages so the agent has conversation memory."""
        if in_thread and thread_ts:
            result = client.conversations_replies(channel=channel, ts=thread_ts, limit=HISTORY_LIMIT)
            return result["messages"]
        # DM: use the channel's recent history (returned newest-first).
        result = client.conversations_history(channel=channel, limit=HISTORY_LIMIT)
        return list(reversed(result["messages"]))

    def run(self) -> None:
        handler = SocketModeHandler(self.app, os.environ["SLACK_APP_TOKEN"])
        logger.info("Slack Claude agent connected as %s — waiting for messages", self.bot_user_id)
        handler.start()


def main() -> None:
    load_dotenv()
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    missing = [v for v in ("SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "ANTHROPIC_API_KEY") if not os.environ.get(v)]
    if missing:
        raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")
    SlackClaudeBot().run()


if __name__ == "__main__":
    main()
