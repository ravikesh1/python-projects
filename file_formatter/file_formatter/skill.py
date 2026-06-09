"""Skill base class and registration decorator.

A *skill* is a single, named text transformation. Subclass :class:`Skill`,
decorate it with :func:`register`, and the formatter will pick it up —
either from the built-in package or from a user skills directory.

Minimal example::

    from file_formatter import Skill, register

    @register
    class Shout(Skill):
        name = "shout"
        description = "Uppercase the whole file"

        def format(self, text: str, path: Path) -> str:
            return text.upper()
"""

from __future__ import annotations

from pathlib import Path


class Skill:
    """Base class for formatting skills.

    Class attributes to set in subclasses:

    - ``name``: unique identifier used on the command line (``--skills name``).
    - ``description``: one-line summary shown by ``list-skills``.
    - ``file_extensions``: extensions this skill applies to, e.g.
      ``(".py", ".txt")``. Leave empty to apply to every file.
    """

    name: str = ""
    description: str = ""
    file_extensions: tuple[str, ...] = ()

    def applies_to(self, path: Path) -> bool:
        """Whether this skill should run on *path* (by default: extension match)."""
        if not self.file_extensions:
            return True
        return path.suffix.lower() in tuple(ext.lower() for ext in self.file_extensions)

    def format(self, text: str, path: Path) -> str:
        """Return the formatted text. Must be overridden by subclasses."""
        raise NotImplementedError(f"{type(self).__name__} must implement format()")


def register(cls: type[Skill]) -> type[Skill]:
    """Class decorator that marks a Skill subclass for discovery."""
    if not (isinstance(cls, type) and issubclass(cls, Skill)):
        raise TypeError("@register can only be applied to Skill subclasses")
    if not cls.name:
        raise ValueError(f"{cls.__name__} must define a non-empty 'name' attribute")
    cls._ff_registered = True
    return cls


def skills_in_module(module: object) -> list[type[Skill]]:
    """Return the @register-marked Skill classes defined in *module*."""
    found = []
    for obj in vars(module).values():
        if (
            isinstance(obj, type)
            and issubclass(obj, Skill)
            and "_ff_registered" in obj.__dict__  # marked directly, not inherited
        ):
            found.append(obj)
    return found
