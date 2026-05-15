"""CLI for the agentic tag workflow: pass a natural-language instruction."""

from __future__ import annotations

import argparse
import sys

from langchain_core.messages import HumanMessage

from tag_system.agent import build_agent


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="tag-agent",
        description=(
            "Orchestrate the tag system via a LangGraph ReAct agent. "
            "Example: tag-agent 'tag and save: I loved the new release'"
        ),
    )
    parser.add_argument("instruction", nargs="?", help="Instruction. Reads stdin if omitted.")
    parser.add_argument("--model", help="Override the Claude model.")
    args = parser.parse_args()

    instruction = args.instruction if args.instruction is not None else sys.stdin.read()
    instruction = instruction.strip()
    if not instruction:
        parser.error("no instruction provided")

    agent = build_agent(model=args.model)
    result = agent.invoke({"messages": [HumanMessage(content=instruction)]})
    print(result["messages"][-1].content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
