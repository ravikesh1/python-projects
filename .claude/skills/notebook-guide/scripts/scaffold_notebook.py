#!/usr/bin/env python3
"""Scaffold a learning notebook with the notebook-guide standard structure.

Writes a valid .ipynb containing the skeleton (title, objectives, setup,
one markdown+code pair per concept section, pitfalls, exercises, recap).
Content is left as clearly marked placeholders to fill in with NotebookEdit.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def md(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source}


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": source,
    }


SETUP_CELL = '''\
# Setup: verify dependencies and environment before anything else.
# If an import fails, run the printed `uv` command from the repo root.
import importlib.util
import os

REQUIRED = []  # e.g. ["numpy", "langchain_core"] -- fill in for this notebook

missing = [pkg for pkg in REQUIRED if importlib.util.find_spec(pkg) is None]
if missing:
    raise SystemExit(
        f"Missing packages: {missing}. Run: uv add --group notebooks " + " ".join(missing)
    )

from dotenv import load_dotenv

load_dotenv()

REQUIRED_ENV = []  # e.g. ["ANTHROPIC_API_KEY"] -- only if this notebook calls an API
missing_env = [v for v in REQUIRED_ENV if not os.getenv(v)]
if missing_env:
    raise SystemExit(f"Set these in your .env file first: {missing_env}")

print("Setup OK")
'''


def build_notebook(title: str, objectives: list[str], sections: list[str]) -> dict:
    objective_lines = "\n".join(f"- {o}" for o in objectives)
    cells = [
        md(
            f"# {title}\n\n"
            "**What you'll learn:**\n\n"
            f"{objective_lines}\n\n"
            "**Time:** ~60-90 minutes | **Prerequisites:** _(fill in)_"
        ),
        md("## Setup\n\n_(One sentence on what we install/import and why.)_"),
        code(SETUP_CELL),
    ]

    for i, section in enumerate(sections, start=1):
        cells.append(
            md(
                f"## {i}. {section}\n\n"
                "_(Explain WHY this matters in <150 words, then the code below "
                "shows the minimal HOW.)_"
            )
        )
        cells.append(code(f"# {section}: minimal runnable example\n"))
        cells.append(
            code(
                f"# Variation: what happens if we change ... ?\n"
                f"# (tweak the example above so the reader sees behavior change)\n"
            )
        )

    cells.extend(
        [
            md(
                "## Common pitfalls\n\n"
                "_(Run at least one broken version so the reader sees the "
                "failure, then show the fix.)_"
            ),
            code("# Pitfall demo: run the broken version first\n"),
            md(
                "## Exercises\n\n"
                "Complete the TODO cells below. Solutions are at the bottom -- "
                "try before peeking!"
            ),
            code("# Exercise 1: TODO\n"),
            code("# Exercise 2: TODO\n"),
            md("<details>\n<summary>Solutions</summary>\n\n_(fill in)_\n\n</details>"),
            md(
                "## Recap & next steps\n\n"
                "_(3-5 bullets of what was learned, link to the next notebook "
                "in the series, and 1-2 further-reading links.)_"
            ),
        ]
    )

    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Output .ipynb path, e.g. notebooks/01_rag.ipynb")
    parser.add_argument("--title", required=True)
    parser.add_argument(
        "--objectives", nargs="+", required=True, help="3-5 learning objectives"
    )
    parser.add_argument(
        "--sections", nargs="+", required=True, help="2-4 concept section titles"
    )
    args = parser.parse_args()

    out = Path(args.path)
    if out.exists():
        sys.exit(f"Refusing to overwrite existing file: {out}")
    if out.suffix != ".ipynb":
        sys.exit(f"Output path must end in .ipynb, got: {out}")

    out.parent.mkdir(parents=True, exist_ok=True)
    notebook = build_notebook(args.title, args.objectives, args.sections)
    out.write_text(json.dumps(notebook, indent=1) + "\n")
    print(f"Scaffolded {out} with {len(notebook['cells'])} cells")


if __name__ == "__main__":
    main()
