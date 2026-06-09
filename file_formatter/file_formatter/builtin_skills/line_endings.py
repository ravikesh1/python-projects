"""Line-ending normalization."""

from __future__ import annotations

from pathlib import Path

from file_formatter.skill import Skill, register


@register
class NormalizeLineEndings(Skill):
    name = "normalize-line-endings"
    description = "Convert CRLF and CR line endings to LF"

    def format(self, text: str, path: Path) -> str:
        return text.replace("\r\n", "\n").replace("\r", "\n")
