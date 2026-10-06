---
name: fix-with-failing-test
description: Fix a reported bug in this integration, starting from a failing test that reproduces it. Use when handling a bug report, a coordinator retry/verify issue, or any "X doesn't work" request with logs or diagnostics.
---

# Fixing a bug, reproduction first

The rule: **no production edit before a test fails for the right reason.** A fix without a reproducing test
cannot be shown to work and cannot stop the bug returning.

## Work order

1. **Locate the seam.** `tests/` mirrors the source layout, so a bug in
   `custom_components/solis_cloud_control/inverters/foo.py` gets its test in `tests/inverters/test_foo.py`.
   Read the diagnostics or logs in the report to pin the CID, the platform, and the inverter kind.

2. **Write the reproducing test first.** Use the existing `tests/conftest.py` fixtures (`mock_api_client`,
   `mock_coordinator`, `mock_config_entry`, `any_inverter_info`, `any_inverter`) rather than new setup.

3. **Confirm it fails for the expected reason.** Run it alone:

   ```bash
   uv run pytest --cov-fail-under=0 tests/inverters/test_foo.py::test_the_bug
   ```

   Read the failure. A test that fails for an unrelated reason (typo, wrong fixture, bad assertion) proves
   nothing — fix the test until the failure *is* the reported bug. Only then continue.

4. **Optionally lock the test down.** Export `SOLIS_LOCK_TESTS=1` before the fix phase and the PreToolUse hook
   will refuse edits under `tests/`, so the reproduction cannot quietly be weakened into passing.

5. **Now fix the source** under `custom_components/`. Smallest change that makes the reproduction pass. Do not
   relax an assertion, widen a tolerance, or delete a case to get green.

6. **Regression scope.** If the same class of bug is reachable through other CIDs or the other inverter kind,
   parametrize the test to cover them.

## Proof of success

The reproducing test passes, unmodified since step 3, and `mise run check` is green including the 98% branch
coverage gate. Unset `SOLIS_LOCK_TESTS` when done.
