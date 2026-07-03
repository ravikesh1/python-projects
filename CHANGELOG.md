# Changelog

Notable changes across this repo, organized by component. Each component
versions independently — headings below are tagged `<component> vX.Y.Z`:

- **mysql-explorer skill** — version tracks `.claude-plugin/plugin.json`
  (kept in sync with the matching entry in `.claude-plugin/marketplace.json`).
  SemVer is applied to *skill guidance*, not code: **patch** =
  wording/typo/non-behavioral fixes, **minor** = new guidance or expanded
  coverage, **major** = a change that could break users' existing
  expectations of how the skill behaves.
- **mcp-mysql-server package** — version tracks `[project] version` in
  `pyproject.toml`. Standard SemVer for code.

## [Unreleased]

## mcp-mysql-server v0.2.0 - 2026-07-03
### Added
- Per-call audit log (opt-in via `MYSQL_AUDIT_LOG=true`, path configurable
  via `MYSQL_AUDIT_LOG_PATH`): one JSONL record per tool call with
  timestamp, tool name, arguments (truncated), outcome, and an anomaly flag.
- Anomaly detection for unexpected argument keys: a tool call carrying keys
  its schema doesn't declare is never blocked (the extra key is ignored, as
  before) but is always logged as a warning, and flagged `anomalous: true`
  in the audit record when auditing is enabled.

## mysql-explorer v0.1.0 - 2026-06-26
- Initial release: discovery-first workflow (`list_databases` →
  `list_tables` → `describe_table`), read-only-by-default guidance,
  opt-in-gated writes/DDL, and row-limit/`truncated` handling.
