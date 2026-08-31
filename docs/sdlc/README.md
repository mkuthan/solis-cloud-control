# Experiment: AI-native SDLC, Build + Test stages

An experiment in applying the Build and Test stages of the
[AI-native SDLC playbook](https://claude.com/blog/the-ai-native-sdlc-playbook) to this repository.

Everything landed in a single commit on `experiment/ai-sdlc-build-test`, so the kill switch is one
`git revert`.

## What problem this addresses

1. **Two sources of truth for conventions.** `.github/instructions/python.instructions.md` held rules that
   `AGENTS.md` did not (logging-level semantics, error-handling policy, "prefer existing conftest fixtures",
   "don't assert on log text"). Those files are Copilot-format, so Claude Code was running with *less*
   project knowledge than Copilot.
2. **Verification was advice, not mechanism.** Nothing made an agent run `mise run check` before claiming
   done.
3. **No encoded knowledge for the most common task.** Adding an entity touches seven files, one of which
   (the hard-coded platform counts in `tests/test_init.py`) fails silently until the end of a full test run.

## What was added

| Artifact | Playbook stage | Purpose |
| --- | --- | --- |
| `AGENTS.md` (rewritten) | Build | Institutional knowledge: verification, definition of done, common mistakes, conventions |
| `.claude/hooks/format-python.sh` | Build | PostToolUse: `ruff format` + `ruff check --fix` on the single edited file |
| `.claude/hooks/verify.sh` | Test | Stop: runs `mise run check` when the tree is dirty, blocks the stop on failure |
| `.claude/hooks/lock-tests.sh` | Test | PreToolUse: makes `tests/` read-only while `SOLIS_LOCK_TESTS=1` |
| `.claude/skills/add-inverter-entity/` | Build | The seven-file work order for entity changes |
| `.claude/skills/fix-with-failing-test/` | Test | Reproduce-before-fix discipline |
| `.claude/settings.json` | Build | Hook wiring, read-only command allowlist, deny rules for `.env` and HA storage |

## Baseline (recorded before any change)

`mise run check` on a clean tree:

- **7.5s** wall clock total (lint 2.4s, format check 2.4s, typecheck 3.8s, tests 2.4s)
- 413 tests passed
- Branch coverage 98.97% against a 98% gate

This is the number that made the Stop hook worth having: full verification costs under 8 seconds, so there is
no reason to let an agent finish unverified.

## Deliberately not done

- **Continuous evals in CI** — authoring 20–50 eval tasks costs more than everything above, and cannot pay off
  before we know whether the skills fire at all.
- **Protected-path and secret-scanning hooks** — a second lock on a door that already has an interactive
  permission prompt and a single reviewer. The one real adjacent risk (an agent *reading* a live API key from
  `.env` or `config/.storage/`) is handled declaratively in `permissions.deny`, which cannot be defeated by a
  missing binary or a PATH quirk.
- **A committed `plan.md`** — the playbook's `plan.md` derives its value from a second human reading the plan
  before code exists. With one maintainer, plan mode already provides the real control (approval before
  execution) and keeps the plan in `~/.claude/plans/`. The part worth keeping, *proof of success*, lives in
  both skills and in the definition of done instead. Revisit if a second contributor appears.
- **A git pre-commit hook or the pre-commit framework** — would be a third layer running the same command.
- **Subagents and git worktrees** — this codebase fits in context whole, and `tests/conftest.py` plus
  `tests/test_init.py` are shared-edit hotspots for the most common task, so parallel worktrees would
  manufacture conflicts.
- **Any change to the coverage gate, ruff rule set, or CI workflows** — changing the measuring instrument
  during the experiment would destroy the before/after comparison.

## How this gets judged

Run three real tasks — one new entity/CID, one new model id, one coordinator bug fix — and record the metrics
in [`experiment-log.md`](experiment-log.md). Do not tune the configuration mid-experiment.

Leading indicators, per task:

1. Did the agent run the full check itself, unprompted, before claiming done?
2. Human correction turns, compared with the pre-experiment control task.
3. Did the relevant skill fire without being named?
4. Stop-hook block rate. High early is good; still high by task 5 means the fix belongs in `AGENTS.md`, not in
   more hooks.
5. Hook tax in seconds per session. If the Stop hook fires on read-only conversations, the dirty-tree guard is
   broken.

Lagging indicators, over the next 5–10 merged PRs:

1. CI red-on-first-push rate (free from `gh run list`) — the single best signal.
2. Follow-up `fix:` commits within 7 days of a `feat:` commit.
3. Entity-task diff completeness without a reminder.
4. Time from a "new inverter support" issue being opened to merge.

## Kill criteria, decided in advance

After three real tasks, revert the specific piece if:

- a skill never auto-fired across the tasks it should have covered — its description is wrong, or it is
  unnecessary; fix it or delete it, do not keep it out of politeness;
- the Stop hook never blocked anything — it is pure tax, so demote it to a documented manual command;
- hook tax exceeds roughly 60s per session.

If correction turns do not drop against the baseline, keep only the `AGENTS.md` changes and revert the rest.
