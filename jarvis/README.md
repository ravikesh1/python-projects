# JARVIS

An Iron Man-style AI assistant powered by the Claude API. Text-first CLI with an
optional voice mode, a witty British-butler persona, and a handful of built-in
tools.

A general-purpose personal assistant: it chats, answers questions, and helps you
stay organised — remembering you across sessions, managing your to-do list and
notes, and reaching for tools (and optionally your database) when they help.

## Features

- **Conversational brain** — Claude Opus 4.8 with a JARVIS persona, streaming
  replies token-by-token in the terminal.
- **Remembers you across sessions** — durable memory of your name, preferences,
  and context, plus a persistent to-do list and notes (`remember_fact`,
  `forget_fact`, `add_task`, `list_tasks`, `complete_task`, `add_note`,
  `list_notes`, `delete_note`). Stored locally under `~/.jarvis/`.
- **Everyday tools** — JARVIS calls these on its own when they help:
  - `get_datetime` — current date/time, optionally in any IANA timezone
  - `calculate` — safe arithmetic (`+ - * / // % **` and parentheses)
  - `get_system_info` — OS, Python, CPU, memory, and disk of the host machine
  - `web_search` — Anthropic-hosted web search for current information
- **Talk to it (voice mode)** — with `--voice`, speak to JARVIS and hear it
  reply, in a continuous back-and-forth conversation.
- **Database access (optional)** — with `--mysql`, JARVIS can also query your
  databases through the bundled MCP MySQL server.

## Setup

This project uses [uv](https://docs.astral.sh/uv/).

```bash
uv sync                 # core (text mode)
uv sync --extra voice   # add speech-to-text + text-to-speech
```

Set your Anthropic API key — copy `.env.example` to `.env` and fill in
`ANTHROPIC_API_KEY`, or export it in your shell.

## Usage

```bash
uv run jarvis                       # interactive text chat
uv run jarvis --once "What time is it in Tokyo?"
uv run jarvis --voice               # speak and listen (needs the voice extra)
uv run jarvis --mysql                # let JARVIS query your MySQL databases
uv run jarvis --effort medium       # trade latency for more reasoning
uv run jarvis --model claude-opus-4-8
```

### Database access (`--mysql`)

`--mysql` launches the repo's [MCP MySQL server](../mcp_mysql_server/) as a
subprocess and exposes its tools to JARVIS, so you can ask things like *"what
tables are in the orders database?"* or *"show me the 5 most recent signups."*

Configure the connection with `MYSQL_*` variables in `.env` (see
`.env.example`). Reads are available by default; writes and DDL stay disabled
unless you set `MYSQL_ALLOW_WRITE=true` / `MYSQL_ALLOW_DDL=true`.

In text mode, type `exit` (or `quit`, `goodbye`) to leave. Run `python -m jarvis`
as an equivalent to `jarvis`.

### Effort

`--effort` controls the latency/quality trade-off (`low` by default for snappy,
voice-friendly replies). Bump it to `medium`/`high` for harder questions.

## Voice mode notes

The `voice` extra installs `SpeechRecognition`, `pyttsx3`, and `PyAudio`. Those
need OS-level audio support:

- **macOS:** `brew install portaudio` then `uv sync --extra voice`
- **Debian/Ubuntu:** `sudo apt install portaudio19-dev espeak`
- Speech-to-text uses Google's free Web Speech endpoint, so a network
  connection is required for transcription.

## Programmatic use

```python
from jarvis import Jarvis

j = Jarvis()
print(j.ask("Calculate 2**10 and tell me a joke about it."))
print(j.ask("What did I just ask you?"))  # remembers context
```
