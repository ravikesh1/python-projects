# Slack Claude Agent

An always-on Slack bot powered by Claude. Once it's running you can:

- **DM the bot** — just open a direct message and chat
- **@mention it in any channel** it's been invited to — it replies in a thread

It remembers context per conversation: in channels it replays the thread, in DMs it replays recent history. Because the memory comes from Slack itself, restarting the bot doesn't lose context.

It uses **Socket Mode**, so it needs no public URL — it runs anywhere with outbound internet (your laptop, a VM, a container).

## 1. Create the Slack app

Go to <https://api.slack.com/apps> → **Create New App** → **From a manifest**, pick your workspace, and paste:

```yaml
display_information:
  name: Claude Agent
  description: An AI assistant powered by Claude
features:
  bot_user:
    display_name: claude-agent
    always_online: true
oauth_config:
  scopes:
    bot:
      - app_mentions:read
      - channels:history
      - groups:history
      - chat:write
      - im:history
      - im:read
      - im:write
      - reactions:write
settings:
  event_subscriptions:
    bot_events:
      - app_mention
      - message.im
  interactivity:
    is_enabled: false
  socket_mode_enabled: true
```

Then collect two tokens:

1. **Bot token** (`xoxb-...`): *OAuth & Permissions* → **Install to Workspace** → copy *Bot User OAuth Token*
2. **App-level token** (`xapp-...`): *Basic Information* → *App-Level Tokens* → **Generate Token** with the `connections:write` scope

## 2. Configure

Copy `.env.example` to `.env` at the repo root and fill in:

| Variable            | Required | Description                                        |
| ------------------- | -------- | -------------------------------------------------- |
| `SLACK_BOT_TOKEN`   | ✅       | `xoxb-...` bot token                               |
| `SLACK_APP_TOKEN`   | ✅       | `xapp-...` app-level token (Socket Mode)           |
| `ANTHROPIC_API_KEY` | ✅       | Anthropic API key                                  |
| `CLAUDE_MODEL`      |          | Defaults to `claude-opus-4-8`                      |
| `CLAUDE_MAX_TOKENS` |          | Max response tokens (default `16000`)              |

## 3. Run

```bash
uv sync
uv run slack-claude-agent
```

You should see `Slack Claude agent connected as U... — waiting for messages`. Then in Slack:

- DM the bot: *"hey, summarize what a vector database is"*
- In a channel (after `/invite @claude-agent`): *"@claude-agent what does this error mean? ..."*

The bot reacts with 👀 while it's thinking, then replies (in a thread when mentioned in a channel).

### Keeping it running

Any process supervisor works. For example with systemd:

```ini
[Unit]
Description=Slack Claude agent
After=network-online.target

[Service]
WorkingDirectory=/path/to/python-projects
ExecStart=/usr/local/bin/uv run slack-claude-agent
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Or in Docker / a screen/tmux session — the bot reconnects automatically if the socket drops.

## How it works

```
Slack (Socket Mode) ──▶ slack_claude_agent/app.py   (Bolt event handlers)
                                │
                                ▼
                       slack_claude_agent/agent.py  (Anthropic SDK)
                                │   model: claude-opus-4-8
                                │   adaptive thinking + prompt caching
                                ▼
                          Claude API ──▶ reply posted back to Slack
```

- On each message it fetches the thread (or DM history), converts it into a Claude conversation (`user`/`assistant` turns), and asks Claude for the next reply.
- The system prompt is cached with `cache_control: ephemeral`, so repeated turns are cheap.
- Long replies are split into multiple Slack messages automatically.
