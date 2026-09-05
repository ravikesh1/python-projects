# Changelog

Notable changes across this repo, organized by component. Right now the only
versioned/released component is the `mysql-explorer` skill — its version
corresponds to the `version` field in `.claude-plugin/plugin.json`, kept in
sync with the matching entry in `.claude-plugin/marketplace.json`. If other
components (e.g. the `mcp-mysql-server` package) get their own release
process later, their entries go here too, tagged by component.

Versioning follows [SemVer](https://semver.org/) as applied to *skill
guidance*, not code: **patch** = wording/typo/non-behavioral fixes, **minor**
= new guidance or expanded coverage, **major** = a change that could break
users' existing expectations of how a skill behaves.

## [Unreleased]
### session activity logging (`.claude/hooks/`)
- Replaced the skill-only usage hook with a session activity logger wired to
  `SessionStart`, `PostToolUse` and `SessionEnd`. It records one line per
  session start/end plus every `Skill` invocation (with invocation level:
  user-invoked vs model-invoked) and every MySQL MCP server tool call (tool,
  database/table, statement, row count / truncation / error), and closes each
  session with a rollup summary.
- Added `.claude/hooks/session_report.py` to read the log back as a per-session
  summary, a single-session timeline, or JSON.
- Log feedback sent through the MySQL MCP server (`report_bug` and friends) as
  its own `feedback` record — severity, category, description, repro context,
  returned report id, and whether the submission succeeded — instead of a
  generic tool call. Rolled into the session summary and readable on its own
  with `session_report.py --feedback`.

## [0.1.0] - 2026-06-26
### mysql-explorer skill
- Initial release: discovery-first workflow (`list_databases` →
  `list_tables` → `describe_table`), read-only-by-default guidance,
  opt-in-gated writes/DDL, and row-limit/`truncated` handling.
