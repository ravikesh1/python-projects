"""Command-line interface for JARVIS: text REPL with an optional voice mode."""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from .assistant import DEFAULT_EFFORT, DEFAULT_MODEL, Jarvis, make_default_client

GREETING = "JARVIS online. How can I help you, sir?"
EXIT_WORDS = {"exit", "quit", "goodbye", "bye", "shutdown", "power down"}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jarvis",
        description="JARVIS — an Iron Man-style AI assistant powered by Claude.",
    )
    parser.add_argument(
        "--voice",
        action="store_true",
        help="Talk to JARVIS with your microphone and hear spoken replies.",
    )
    parser.add_argument(
        "--once",
        metavar="MESSAGE",
        help="Send a single message, print the reply, and exit.",
    )
    parser.add_argument(
        "--mysql",
        action="store_true",
        help=(
            "Give JARVIS access to your databases via the bundled MCP MySQL "
            "server (configure MYSQL_* in .env)."
        ),
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Claude model ID (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--effort",
        default=DEFAULT_EFFORT,
        choices=["low", "medium", "high", "xhigh", "max"],
        help=f"Reasoning effort / latency trade-off (default: {DEFAULT_EFFORT}).",
    )
    return parser


def _make_jarvis(args: argparse.Namespace, mcp_provider=None) -> Jarvis:
    client = make_default_client()
    return Jarvis(
        client=client,
        model=args.model,
        effort=args.effort,
        mcp_provider=mcp_provider,
    )


def _run_once(jarvis: Jarvis, message: str) -> None:
    reply = jarvis.ask(message)
    print(reply)


def _run_text_repl(jarvis: Jarvis) -> None:
    print(GREETING)
    while True:
        try:
            user_text = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nJARVIS: Powering down. Until next time, sir.")
            return

        if not user_text:
            continue
        if user_text.lower() in EXIT_WORDS:
            print("JARVIS: Powering down. Until next time, sir.")
            return

        print("JARVIS: ", end="", flush=True)
        jarvis.ask(
            user_text,
            on_text=lambda chunk: print(chunk, end="", flush=True),
            on_tool=lambda name: print(f"\n  [using {name}…] ", end="", flush=True),
        )
        print()


def _run_voice_repl(jarvis: Jarvis) -> None:
    from .voice import VoiceIO  # lazy: keeps text mode dependency-free

    voice = VoiceIO()
    print(GREETING)
    voice.speak(GREETING)

    while True:
        print("\n[listening… say 'goodbye' to stop]")
        try:
            user_text = voice.listen().strip()
        except KeyboardInterrupt:
            break

        if not user_text:
            continue

        print(f"you> {user_text}")
        if user_text.lower() in EXIT_WORDS:
            farewell = "Powering down. Until next time, sir."
            print(f"JARVIS: {farewell}")
            voice.speak(farewell)
            return

        print("JARVIS: ", end="", flush=True)
        reply = jarvis.ask(
            user_text,
            on_text=lambda chunk: print(chunk, end="", flush=True),
        )
        print()
        voice.speak(reply)


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = _build_parser().parse_args(argv)

    mcp_provider = None
    if args.mysql:
        try:
            from .mcp_bridge import mysql_provider

            print("Connecting to the MCP MySQL server…", file=sys.stderr)
            mcp_provider = mysql_provider().start()
            tools = ", ".join(t["name"] for t in mcp_provider.tool_specs())
            print(f"Database tools available: {tools}", file=sys.stderr)
        except Exception as exc:
            print(f"Error: could not start the MySQL MCP server: {exc}", file=sys.stderr)
            return 1

    try:
        jarvis = _make_jarvis(args, mcp_provider=mcp_provider)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        if mcp_provider is not None:
            mcp_provider.close()
        return 1

    try:
        if args.once is not None:
            _run_once(jarvis, args.once)
        elif args.voice:
            _run_voice_repl(jarvis)
        else:
            _run_text_repl(jarvis)
    except RuntimeError as exc:  # e.g. voice extras missing
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        if mcp_provider is not None:
            mcp_provider.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
