"""Whitespace cleanup skills."""

from __future__ import annotations

from pathlib import Path

from file_formatter.skill import Skill, register


@register
class StripTrailingWhitespace(Skill):
    name = "strip-trailing-whitespace"
    description = "Remove spaces and tabs at the end of each line"

    def format(self, text: str, path: Path) -> str:
        return "\n".join(line.rstrip(" \t") for line in text.split("\n"))


@register
class EnsureFinalNewline(Skill):
    name = "ensure-final-newline"
    description = "Make sure the file ends with exactly one newline"

    def format(self, text: str, path: Path) -> str:
        if not text:
            return text
        return text.rstrip("\n") + "\n"


@register
class TabsToSpaces(Skill):
    name = "tabs-to-spaces"
    description = "Replace leading tabs with 4 spaces"
    tab_width = 4

    def format(self, text: str, path: Path) -> str:
        out = []
        for line in text.split("\n"):
            stripped = line.lstrip("\t")
            n_tabs = len(line) - len(stripped)
            out.append(" " * (self.tab_width * n_tabs) + stripped)
        return "\n".join(out)


@register
class CollapseBlankLines(Skill):
    name = "collapse-blank-lines"
    description = "Collapse runs of 3+ blank lines down to 2"

    def format(self, text: str, path: Path) -> str:
        out: list[str] = []
        blanks = 0
        for line in text.split("\n"):
            if line.strip() == "":
                blanks += 1
                if blanks > 2:
                    continue
            else:
                blanks = 0
            out.append(line)
        return "\n".join(out)
