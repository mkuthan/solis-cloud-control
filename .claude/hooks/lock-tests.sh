#!/usr/bin/env bash
# PreToolUse hook: refuse edits under tests/ while SOLIS_LOCK_TESTS=1.
# Opt-in on purpose -- most changes in this repo legitimately touch tests/.
# Enable it during a bug fix so the reproducing test cannot be weakened.
set -uo pipefail

[[ "${SOLIS_LOCK_TESTS:-0}" == "1" ]] || exit 0

file="$(jq -r '.tool_input.file_path // empty' 2>/dev/null)"
[[ -n "$file" ]] || exit 0

case "$file" in
*/tests/* | tests/*)
  echo "SOLIS_LOCK_TESTS=1 is set: tests/ is read-only. Fix the source, not the test that reproduces the bug." >&2
  exit 2
  ;;
esac

exit 0
