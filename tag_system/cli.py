"""Command-line entry point: read text from argv or stdin and print tags as JSON."""

from __future__ import annotations

import argparse
import sys

from tag_system.tagger import Tagger


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="tag-text",
        description="Tag a piece of text using an LLM (sentiment, language, topics, ...).",
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Text to tag. If omitted, read from stdin.",
    )
    parser.add_argument(
        "--model",
        help="Override the Claude model (defaults to TAG_MODEL env or claude-sonnet-4-5).",
    )
    args = parser.parse_args()

    text = args.text if args.text is not None else sys.stdin.read()
    text = text.strip()
    if not text:
        parser.error("no input text provided")

    tags = Tagger(model=args.model).tag(text)
    print(tags.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
