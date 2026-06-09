"""Skill discovery: built-in skills plus user skills loaded from directories.

User skills are plain ``.py`` files dropped into a skills directory. Search
order (later wins on name collisions, so user skills can override built-ins):

1. Built-in skills (``file_formatter.builtin_skills``)
2. ``~/.file_formatter/skills/``
3. ``./skills/`` relative to the current working directory
4. ``$FILE_FORMATTER_SKILLS_DIR`` (``os.pathsep``-separated list of dirs)
5. Any ``--skills-dir`` passed on the command line
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import pkgutil
import sys
from pathlib import Path

from file_formatter import builtin_skills
from file_formatter.skill import Skill, skills_in_module


class SkillLoadError(Exception):
    """Raised when a user skill file cannot be imported."""


def default_skill_dirs() -> list[Path]:
    dirs = [
        Path.home() / ".file_formatter" / "skills",
        Path.cwd() / "skills",
    ]
    env = os.environ.get("FILE_FORMATTER_SKILLS_DIR", "")
    for entry in env.split(os.pathsep):
        if entry.strip():
            dirs.append(Path(entry.strip()).expanduser())
    return dirs


def _load_builtin_skills() -> list[type[Skill]]:
    skills: list[type[Skill]] = []
    for info in pkgutil.iter_modules(builtin_skills.__path__):
        module = importlib.import_module(f"{builtin_skills.__name__}.{info.name}")
        skills.extend(skills_in_module(module))
    return skills


def _load_skill_file(path: Path) -> list[type[Skill]]:
    module_name = f"_file_formatter_user_skill_{path.stem}_{abs(hash(str(path)))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise SkillLoadError(f"cannot load skill file: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # surface the offending file, not just the traceback
        raise SkillLoadError(f"error importing skill file {path}: {exc}") from exc
    return skills_in_module(module)


def _load_dir_skills(directory: Path) -> list[type[Skill]]:
    skills: list[type[Skill]] = []
    if not directory.is_dir():
        return skills
    for path in sorted(directory.glob("*.py")):
        if path.name.startswith("_"):
            continue
        skills.extend(_load_skill_file(path))
    return skills


def load_skills(extra_dirs: list[Path] | None = None) -> dict[str, Skill]:
    """Load all skills and return them as ``{name: instance}``.

    Later sources override earlier ones on name collisions.
    """
    registry: dict[str, Skill] = {}
    for cls in _load_builtin_skills():
        registry[cls.name] = cls()
    for directory in default_skill_dirs() + list(extra_dirs or []):
        for cls in _load_dir_skills(directory):
            registry[cls.name] = cls()
    return registry
