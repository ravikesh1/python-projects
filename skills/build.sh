#!/usr/bin/env bash
#
# Build the upload-ready Skill archive for the Claude desktop app.
#
# Produces dist/mysql-explorer.zip whose top level is the `mysql-explorer/`
# folder containing SKILL.md — the layout the desktop "Upload skill" flow expects.
#
# Usage:
#   bash skills/build.sh
#
# Then in the Claude desktop app:
#   Settings -> Capabilities -> Skills -> Upload  (select dist/mysql-explorer.zip)
#
# Re-run this and re-upload whenever you change the skill; the desktop app does
# not auto-sync from GitHub.

set -euo pipefail

SKILL_NAME="mysql-explorer"

# Resolve paths relative to this script so it works from any CWD.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SKILL_DIR="${SCRIPT_DIR}/${SKILL_NAME}"
DIST_DIR="${REPO_ROOT}/dist"
OUT_ZIP="${DIST_DIR}/${SKILL_NAME}.zip"

if [[ ! -f "${SKILL_DIR}/SKILL.md" ]]; then
  echo "error: ${SKILL_DIR}/SKILL.md not found" >&2
  exit 1
fi

if ! command -v zip >/dev/null 2>&1; then
  echo "error: 'zip' is required but not installed" >&2
  exit 1
fi

mkdir -p "${DIST_DIR}"
rm -f "${OUT_ZIP}"

# Zip from skills/ so the archive contains the `mysql-explorer/` directory at its
# top level. Exclude OS cruft.
( cd "${SCRIPT_DIR}" && zip -r -q "${OUT_ZIP}" "${SKILL_NAME}" -x '*.DS_Store' )

echo "Built ${OUT_ZIP}"
echo
echo "Contents:"
unzip -l "${OUT_ZIP}"
