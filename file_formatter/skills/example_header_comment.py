"""Example custom skill — copy this pattern to create your own.

Any ``.py`` file in this directory (or ``~/.file_formatter/skills/``, or a
``--skills-dir``) that registers a Skill subclass is loaded automatically.
"""

from pathlib import Path

from file_formatter import Skill, register


@register
class HeaderComment(Skill):
    name = "header-comment"
    description = "Add a '# File: <name>' header to Python files that lack one"
    file_extensions = (".py",)

    def format(self, text: str, path: Path) -> str:
        header = f"# File: {path.name}"
        if text.startswith(header):
            return text
        return f"{header}\n{text}"
