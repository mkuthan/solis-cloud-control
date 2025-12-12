---
description: 'Python coding conventions and guidelines'
applyTo: '**/*.py'
---

# Python Coding Conventions (Repository Aligned)

These instructions refine the generic Python guidance to match the project specific rules defined in `copilot-instructions.md`.

## Core Principles

- Target Python 3.13 only; do not use syntax or stdlib features newer than 3.13.
- Follow existing patterns in `custom_components/solis_cloud_control` before introducing new ones.
- Prefer clarity, consistency, and minimalism over exhaustive commentary.
- Avoid external dependencies beyond those already declared in `pyproject.toml`.

## Typing & Naming

- Use modern union syntax (`str | None`), not `Optional[str]` unless already present.
- Prefer built‑in generic types (`list[int]`, `dict[str, float]`) – do NOT reintroduce `List[...]` / `Dict[...]` forms from `typing` unless required for compatibility.
- Keep function names descriptive and concise; avoid abbreviations unless ubiquitous (`cid`, `uid`).
- Module private helpers: prefix with `_`.

## Docstrings & Comments

- Keep docstrings sparse; only add when behavior or transformation is non-obvious.
- Do not add boilerplate docstrings for trivial getters or simple passthroughs.
- Add a short comment when parsing / bitmask / retry logic is non-trivial; focus on the "why" not restating the code.

## Formatting & Style

- Use parameterized logging: `_LOGGER.debug("Fetched %d items", count)` (avoid f-strings inside log methods unless unavoidable).
- Keep imports minimal and standard library only (unless existing dependency already present).
- Maintain existing file ordering conventions (constants, classes, functions) – mirror current modules.

## Error Handling

- Gracefully handle parse / validation anomalies by returning `None` and logging at `warning` level; avoid raising unless action cannot proceed.
- Propagate API exceptions upward to existing handlers; do not swallow unexpectedly.

## Testing

- New logic must be covered to maintain >= 98% coverage (see pytest addopts).
- Use parametrized tests for boundary, `None`, invalid, and rounding cases.
- Prefer fixtures already defined in `tests/conftest.py` for coordinator / inverter setup.
- Avoid asserting on log text; assert observable outcomes (return values, coordinator control calls, state changes).

## Performance & Side Effects

- Avoid redundant API calls; reuse coordinator data access patterns.
- Keep per-property computations O(1) and lightweight (simple arithmetic / parsing only).

## Logging Levels

- `debug`: verbose internal state snapshots.
- `info`: user-triggered control changes.
- `warning`: unexpected / invalid data scenarios or retry notices.
- `error`: unrecoverable failures or integration-level faults.