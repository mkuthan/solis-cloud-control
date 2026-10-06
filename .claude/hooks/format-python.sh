#!/usr/bin/env bash
# PostToolUse hook: format the single Python file that was just edited.
# Never exits non-zero -- a blocking formatter turns a cosmetic issue into a stuck session.
# Residual violations are caught by the Stop hook and by CI.
set -uo pipefail

file="$(jq -r '.tool_input.file_path // empty' 2>/dev/null)"

[[ -n "$file" && "$file" == *.py && -f "$file" ]] || exit 0

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
command -v uv >/dev/null 2>&1 || exit 0

# Safe fixes only: no --unsafe-fixes, and scoped to the one file.
uv run ruff format -q "$file" >/dev/null 2>&1
uv run ruff check -q --fix "$file" >/dev/null 2>&1

exit 0
