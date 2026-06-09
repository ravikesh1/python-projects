"""Pretty-print JSON files."""

from __future__ import annotations

import json
from pathlib import Path

from file_formatter.skill import Skill, register


@register
class JsonPretty(Skill):
    name = "json-pretty"
    description = "Reindent JSON files with 2-space indentation"
    file_extensions = (".json",)
    indent = 2

    def format(self, text: str, path: Path) -> str:
        data = json.loads(text)
        return json.dumps(data, indent=self.indent, ensure_ascii=False) + "\n"
