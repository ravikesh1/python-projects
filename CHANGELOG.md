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

## [0.1.0] - 2026-06-26
### mysql-explorer skill
- Initial release: discovery-first workflow (`list_databases` →
  `list_tables` → `describe_table`), read-only-by-default guidance,
  opt-in-gated writes/DDL, and row-limit/`truncated` handling.
