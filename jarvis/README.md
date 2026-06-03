# JARVIS

An Iron Man-style AI assistant powered by the Claude API. Text-first CLI with an
optional voice mode, a witty British-butler persona, and a handful of built-in
tools.

## Features

- **Conversational brain** — Claude Opus 4.8 with a JARVIS persona, streaming
  replies token-by-token in the terminal.
- **Tools** — JARVIS calls these on its own when they help:
  - `get_datetime` — current date/time, optionally in any IANA timezone
  - `calculate` — safe arithmetic (`+ - * / // % **` and parentheses)
  - `get_system_info` — OS, Python, CPU, memory, and disk of the host machine
  - `web_search` — Anthropic-hosted web search for current information
- **Voice mode (optional)** — talk to JARVIS and hear it reply.
- **Multi-turn memory** — remembers the conversation within a session.

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
uv run jarvis --effort medium       # trade latency for more reasoning
uv run jarvis --model claude-opus-4-8
```

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
