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

- Line length: 120 characters (matches Ruff configuration), not 79.
- 4 spaces indentation; no tabs.
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

## Example (Aligned)

Below illustrates preferred concise style (no excessive docstring for obvious logic, parameterized logging):

```python
import logging

_LOGGER = logging.getLogger(__name__)

def calculate_area(radius: float) -> float:
    # Circle area: π r^2 (kept inline – trivial formula)
    import math
    if radius < 0:
        _LOGGER.warning("Negative radius provided: %f", radius)
        return 0.0
    return math.pi * radius * radius
```

## When To Add More Documentation

Add a docstring or extended comment if:
- The function encodes inverter register packing / bitmask logic.
- There is non-obvious retry / verification sequencing.
- A transformation depends on subtle Home Assistant API expectations.

Otherwise rely on clear names and small functions.

## Anti-Patterns To Avoid

- Reintroducing legacy typing forms (`List`, `Dict`) where built-ins suffice.
- Blanket docstrings that restate every parameter / return for trivial helpers.
- f-strings inside log calls (except when formatting cannot be parameterized cleanly).
- Broad `except Exception` without re-raising or narrowing.

Adhering to the above keeps this integration internally consistent and maintainable.
