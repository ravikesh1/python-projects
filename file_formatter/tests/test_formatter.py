"""Tests for the pluggable file formatter (stdlib unittest, no extra deps)."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from file_formatter.builtin_skills.json_pretty import JsonPretty
from file_formatter.builtin_skills.line_endings import NormalizeLineEndings
from file_formatter.builtin_skills.whitespace import (
    CollapseBlankLines,
    EnsureFinalNewline,
    StripTrailingWhitespace,
    TabsToSpaces,
)
from file_formatter.cli import main
from file_formatter.registry import load_skills

DUMMY = Path("dummy.txt")


class BuiltinSkillTests(unittest.TestCase):
    def test_strip_trailing_whitespace(self):
        self.assertEqual(
            StripTrailingWhitespace().format("a  \nb\t\nc\n", DUMMY), "a\nb\nc\n"
        )

    def test_ensure_final_newline(self):
        skill = EnsureFinalNewline()
        self.assertEqual(skill.format("a", DUMMY), "a\n")
        self.assertEqual(skill.format("a\n\n\n", DUMMY), "a\n")
        self.assertEqual(skill.format("", DUMMY), "")

    def test_tabs_to_spaces(self):
        self.assertEqual(TabsToSpaces().format("\tx\n\t\ty\n", DUMMY), "    x\n        y\n")

    def test_collapse_blank_lines(self):
        self.assertEqual(
            CollapseBlankLines().format("a\n\n\n\n\nb\n", DUMMY), "a\n\n\nb\n"
        )

    def test_normalize_line_endings(self):
        self.assertEqual(
            NormalizeLineEndings().format("a\r\nb\rc\n", DUMMY), "a\nb\nc\n"
        )

    def test_json_pretty(self):
        out = JsonPretty().format('{"b":1,"a":[1,2]}', Path("x.json"))
        self.assertEqual(out, '{\n  "b": 1,\n  "a": [\n    1,\n    2\n  ]\n}\n')

    def test_json_pretty_only_applies_to_json(self):
        skill = JsonPretty()
        self.assertTrue(skill.applies_to(Path("x.json")))
        self.assertFalse(skill.applies_to(Path("x.py")))


class RegistryTests(unittest.TestCase):
    def test_builtins_are_discovered(self):
        registry = load_skills()
        for name in (
            "strip-trailing-whitespace",
            "ensure-final-newline",
            "tabs-to-spaces",
            "collapse-blank-lines",
            "normalize-line-endings",
            "json-pretty",
        ):
            self.assertIn(name, registry)

    def test_user_skill_dir_is_loaded_and_overrides(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_file = Path(tmp) / "my_skill.py"
            skill_file.write_text(
                "from pathlib import Path\n"
                "from file_formatter import Skill, register\n"
                "@register\n"
                "class Mine(Skill):\n"
                "    name = 'reverse-lines'\n"
                "    description = 'reverse line order'\n"
                "    def format(self, text, path):\n"
                "        return '\\n'.join(reversed(text.split('\\n')))\n"
            )
            registry = load_skills([Path(tmp)])
            self.assertIn("reverse-lines", registry)
            self.assertEqual(
                registry["reverse-lines"].format("a\nb", DUMMY), "b\na"
            )


class CliTests(unittest.TestCase):
    def setUp(self):
        self._cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)  # keep ./skills lookup away from the repo

    def tearDown(self):
        os.chdir(self._cwd)
        self.tmp.cleanup()

    def test_format_in_place(self):
        target = Path(self.tmp.name) / "f.txt"
        target.write_text("hello  \nworld\t")
        rc = main(["format", str(target)])
        self.assertEqual(rc, 0)
        self.assertEqual(target.read_text(), "hello\nworld\n")

    def test_check_mode_exits_nonzero_without_writing(self):
        target = Path(self.tmp.name) / "f.txt"
        target.write_text("hello  \n")
        rc = main(["format", str(target), "--check"])
        self.assertEqual(rc, 1)
        self.assertEqual(target.read_text(), "hello  \n")

    def test_skill_selection(self):
        target = Path(self.tmp.name) / "f.txt"
        target.write_text("hello  ")
        rc = main(["format", str(target), "--skills", "strip-trailing-whitespace"])
        self.assertEqual(rc, 0)
        self.assertEqual(target.read_text(), "hello")  # no final newline added

    def test_new_skill_scaffold_loads(self):
        skills_dir = Path(self.tmp.name) / "custom"
        rc = main(["new-skill", "my-cool-skill", "--dir", str(skills_dir)])
        self.assertEqual(rc, 0)
        scaffold = skills_dir / "my_cool_skill.py"
        self.assertTrue(scaffold.exists())
        registry = load_skills([skills_dir])
        self.assertIn("my-cool-skill", registry)

    def test_unknown_skill_errors(self):
        target = Path(self.tmp.name) / "f.txt"
        target.write_text("x")
        with self.assertRaises(SystemExit):
            main(["format", str(target), "--skills", "nope"])


if __name__ == "__main__":
    unittest.main()
