#!/usr/bin/env bash
# Stop hook: run the full verification loop before the agent is allowed to finish,
# but only when the working tree actually changed.
set -uo pipefail

input="$(cat)"

# Mandatory loop guard: without this, a persistently failing check loops the agent forever.
if [[ "$(printf '%s' "$input" | jq -r '.stop_hook_active // false' 2>/dev/null)" == "true" ]]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

# Nothing changed -> nothing to verify. Keeps read-only conversations free.
if git diff --quiet 2>/dev/null &&
  git diff --cached --quiet 2>/dev/null &&
  [[ -z "$(git ls-files --others --exclude-standard 2>/dev/null)" ]]; then
  exit 0
fi

# Fail open: mise is a shell function in some setups and may not resolve in a
# non-interactive shell. CI is the backstop.
if ! command -v mise >/dev/null 2>&1; then
  echo "verify.sh: mise not found on PATH, skipping verification (CI will catch it)" >&2
  exit 0
fi

output="$(mise run check 2>&1)"
status=$?

if [[ $status -ne 0 ]]; then
  # A blind tail is useless: pytest runs with -rA, which dumps captured output for
  # every test (passing ones included) plus a coverage table, so the real failure
  # scrolls far out of view. Keep the lint/typecheck lines in full -- their
  # diagnostics are already concise -- and for the test task keep only the short
  # summary section, which is the part that names what failed.
  digest="$(printf '%s\n' "$output" | awk '
    /^\[test\] =+ short test summary info/ { in_summary = 1 }
    /^\[test\] PASSED /  { next }   # -rA lists every passing test in the summary too
    /^\[test\]/ {
      if (in_summary) print
      else if ($0 ~ /FAILED|^\[test\] ERROR|[0-9]+ (failed|error)/) print
      next
    }
    /\$ uv run/ { next }
    { print }
  ' | tail -40)"

  {
    echo "Verification failed: 'mise run check' exited with $status."
    echo "Fix this before finishing."
    echo
    printf '%s\n' "${digest:-$(printf '%s\n' "$output" | tail -20)}"
    echo
    echo "Run 'mise run check' for the full output."
  } >&2
  exit 2
fi

exit 0
