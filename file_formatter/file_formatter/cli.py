"""Command-line interface for the pluggable file formatter.

Commands:

- ``format PATH... [--skills a,b] [--check] [--skills-dir DIR]``
- ``list-skills [--skills-dir DIR]``
- ``new-skill NAME [--dir DIR]`` — scaffold a custom skill you can edit
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from file_formatter.registry import SkillLoadError, load_skills
from file_formatter.skill import Skill

SKILL_TEMPLATE = '''"""Custom skill: {name}.

Drop this file in a skills directory and it is picked up automatically:
~/.file_formatter/skills/, ./skills/, $FILE_FORMATTER_SKILLS_DIR,
or any directory passed via --skills-dir.
"""

from pathlib import Path

from file_formatter import Skill, register


@register
class {class_name}(Skill):
    name = "{name}"
    description = "TODO: one-line description of what this skill does"
    # Limit to certain file types, or leave empty to apply to all files:
    file_extensions = ()

    def format(self, text: str, path: Path) -> str:
        # TODO: transform and return the file content.
        return text
'''


def _select_skills(registry: dict[str, Skill], names: str | None) -> list[Skill]:
    if not names:
        return list(registry.values())
    selected = []
    for name in (n.strip() for n in names.split(",") if n.strip()):
        if name not in registry:
            available = ", ".join(sorted(registry))
            raise SystemExit(f"error: unknown skill '{name}' (available: {available})")
        selected.append(registry[name])
    return selected


def _iter_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(p for p in sorted(path.rglob("*")) if p.is_file())
        elif path.is_file():
            files.append(path)
        else:
            raise SystemExit(f"error: no such file or directory: {raw}")
    return files


def cmd_format(args: argparse.Namespace) -> int:
    registry = load_skills([Path(d) for d in args.skills_dir])
    skills = _select_skills(registry, args.skills)
    changed = 0
    for path in _iter_files(args.paths):
        try:
            original = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # skip binary/unreadable files
        text = original
        for skill in skills:
            if not skill.applies_to(path):
                continue
            try:
                text = skill.format(text, path)
            except Exception as exc:
                print(f"{path}: skill '{skill.name}' failed: {exc}", file=sys.stderr)
        if text != original:
            changed += 1
            if args.check:
                print(f"would reformat: {path}")
            else:
                path.write_text(text, encoding="utf-8")
                print(f"reformatted: {path}")
    if args.check:
        if changed:
            print(f"{changed} file(s) would be reformatted")
            return 1
        print("all files already formatted")
        return 0
    print(f"{changed} file(s) reformatted")
    return 0


def cmd_list_skills(args: argparse.Namespace) -> int:
    registry = load_skills([Path(d) for d in args.skills_dir])
    width = max((len(name) for name in registry), default=0)
    for name in sorted(registry):
        skill = registry[name]
        exts = f"  [{', '.join(skill.file_extensions)}]" if skill.file_extensions else ""
        print(f"{name:<{width}}  {skill.description}{exts}")
    return 0


def cmd_new_skill(args: argparse.Namespace) -> int:
    name = args.name.strip().lower().replace("_", "-").replace(" ", "-")
    if not name.replace("-", "").isalnum():
        raise SystemExit(f"error: invalid skill name '{args.name}' (use letters, digits, dashes)")
    target_dir = Path(args.dir).expanduser()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{name.replace('-', '_')}.py"
    if target.exists():
        raise SystemExit(f"error: {target} already exists")
    class_name = "".join(part.capitalize() for part in name.split("-"))
    target.write_text(SKILL_TEMPLATE.format(name=name, class_name=class_name), encoding="utf-8")
    print(f"created {target}")
    print("Edit the format() method, then it is picked up automatically.")
    print(f"Try it: file-formatter format <files> --skills {name} --skills-dir {target_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="file-formatter",
        description="Pluggable file formatter — add your own skills as plain Python files.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_format = sub.add_parser("format", help="format files in place")
    p_format.add_argument("paths", nargs="+", help="files or directories to format")
    p_format.add_argument("--skills", help="comma-separated skill names (default: all)")
    p_format.add_argument("--check", action="store_true",
                          help="don't write; exit 1 if files would change")
    p_format.add_argument("--skills-dir", action="append", default=[],
                          help="extra directory to load skills from (repeatable)")
    p_format.set_defaults(func=cmd_format)

    p_list = sub.add_parser("list-skills", help="list available skills")
    p_list.add_argument("--skills-dir", action="append", default=[],
                        help="extra directory to load skills from (repeatable)")
    p_list.set_defaults(func=cmd_list_skills)

    p_new = sub.add_parser("new-skill", help="scaffold a new custom skill")
    p_new.add_argument("name", help="skill name, e.g. my-formatter")
    p_new.add_argument("--dir", default=str(Path.home() / ".file_formatter" / "skills"),
                       help="directory to create the skill in (default: ~/.file_formatter/skills)")
    p_new.set_defaults(func=cmd_new_skill)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except SkillLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
