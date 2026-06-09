# file-formatter

A pluggable file formatter where each transformation is a **skill** — a small
Python class you can write yourself and drop into a folder. No packaging, no
entry points, no registration files: save a `.py` file and it's available.

## Install

From this directory:

```bash
uv sync          # or: pip install -e .
uv run file-formatter --help
```

Or run without installing:

```bash
PYTHONPATH=. python -m file_formatter.cli --help
```

## Usage

```bash
# Format files or whole directories in place with all applicable skills
file-formatter format src/ notes.txt

# Run only specific skills
file-formatter format src/ --skills strip-trailing-whitespace,ensure-final-newline

# CI mode: change nothing, exit 1 if anything would be reformatted
file-formatter format src/ --check

# See every available skill (built-in + yours)
file-formatter list-skills
```

## Built-in skills

| Skill                       | What it does                                  |
| --------------------------- | --------------------------------------------- |
| `strip-trailing-whitespace` | Remove spaces/tabs at the end of each line    |
| `ensure-final-newline`      | End the file with exactly one newline         |
| `tabs-to-spaces`            | Replace leading tabs with 4 spaces            |
| `collapse-blank-lines`      | Collapse runs of 3+ blank lines down to 2     |
| `normalize-line-endings`    | Convert CRLF / CR to LF                       |
| `json-pretty`               | Reindent `.json` files with 2-space indent    |

## Creating your own skill

Scaffold one (created in `~/.file_formatter/skills/` by default):

```bash
file-formatter new-skill remove-print-statements
```

Then edit the generated file — a skill is just this:

```python
from pathlib import Path
from file_formatter import Skill, register

@register
class RemovePrintStatements(Skill):
    name = "remove-print-statements"
    description = "Delete lines that are bare print() calls"
    file_extensions = (".py",)   # leave empty to apply to all files

    def format(self, text: str, path: Path) -> str:
        return "\n".join(
            line for line in text.split("\n")
            if not line.strip().startswith("print(")
        )
```

Save it and it shows up immediately:

```bash
file-formatter list-skills
file-formatter format src/ --skills remove-print-statements
```

### Where skills are loaded from

In order (later wins, so your skills can override built-ins by reusing a name):

1. Built-in skills
2. `~/.file_formatter/skills/`
3. `./skills/` in the current working directory
4. Directories in `$FILE_FORMATTER_SKILLS_DIR` (separated by `:`)
5. Any `--skills-dir DIR` flags (repeatable)

Files starting with `_` are ignored. See `skills/example_header_comment.py`
for a working example you can copy.

### Skill API

- `name` — unique CLI identifier (kebab-case by convention)
- `description` — one-liner shown by `list-skills`
- `file_extensions` — tuple like `(".py", ".md")`; empty means all files
- `applies_to(path)` — override for custom matching beyond extensions
- `format(text, path)` — return the transformed file content

A skill that raises an exception on a file is reported on stderr and skipped;
other skills and files keep going. Binary/non-UTF-8 files are skipped.

## Tests

```bash
python -m unittest discover -s tests
```
