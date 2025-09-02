# GitHub Copilot Instructions

## Priority Guidelines

When generating code for this repository:

1. Version Compatibility: Target Python 3.13 only (pyproject.toml -> requires-python ~=3.13); do not use syntax or stdlib features introduced after 3.13, and keep Home Assistant APIs compatible with homeassistant==2025.3.3.
2. Context Files: Prefer guidance in this file; no other copilot guidance files exist yet.
3. Codebase Patterns: Mirror patterns from existing integration modules under `custom_components/solis_cloud_control` and tests under `tests`.
4. Architectural Consistency: Maintain a single Home Assistant custom integration architecture with clear separation: API client / inverter domain model / coordinator / platform entity implementations (number, sensor, switch, select, text) / config flow / diagnostics.
5. Code Quality: Prioritize maintainability, testability, and performance while matching existing simplicity. Follow logging, typing, and retry patterns already used.

## Technology Version Detection

Observed versions:
- Python: `~=3.13` (restrict features accordingly).
- Home Assistant Core library: `homeassistant==2025.3.3`.
- Tooling: `pytest-homeassistant-custom-component==0.13.224`, `ruff==0.11.5`.

Implications:
- Use structural pattern matching only if already present (currently NOT used – avoid introducing unless necessary).
- Maintain current style of type hints (PEP 604 union syntax is used, e.g. `str | None`).
- Avoid introducing external dependencies beyond what `pyproject.toml` specifies.

## Architecture & Module Boundaries

Layers/components (implicit from structure):
- `api/`: Low-level Solis Cloud API client & error types.
- `inverters/` & `domain/`: Domain model abstractions (value objects, bitfields, configuration holders) for inverter capabilities.
- `coordinator.py`: Data retrieval + control orchestration with retry & verification loops.
- `entity.py`: Base entity tying coordinator data to Home Assistant entities (availability logic).
- Platform files (`number.py`, `sensor.py`, `switch.py`, `select.py`, `text.py`): Entity classes mapping domain model CIDs to HA platform features with consistent naming and logging.
- `config_flow.py`: User onboarding (two-step: credentials -> inverter selection) with error mapping.
- `diagnostics.py`: Redacted diagnostic dump (serial number masked) using `asdict` from dataclasses.
- `__init__.py`: Integration setup, device registration, migration logic, coordinator instantiation.

Guidance:
- Keep public surface minimal; prefer module-internal helpers (prefix underscore) for creation logic local to files when not reused.
- Pass coordinator plus inverter/domain objects into entities; avoid direct API usage inside entities.
- Maintain retry constants in coordinator; expose control methods only there.

## Codebase Patterns

Naming:
- Entities keys: lowercase with underscores, semantic (e.g. `battery_max_charge_soc`).
- Class names: PascalCase, often prefixed with domain concept (e.g. `BatteryCurrentV1`).
- Private helpers: leading underscore (e.g. `_create_api_client`).

Logging:
- Use module-level `_LOGGER = logging.getLogger(__name__)`.
- Levels: `debug` for data snapshots, `info` for user-triggered control changes, `warning` for invalid/unexpected state or retries.
- String interpolation: always parameterized logging (`_LOGGER.info("Set '%s' to %f", self.name, value)`).

Error Handling:
- Domain parsing returns `None` -> log warning and gracefully skip without raising (e.g., invalid storage mode / malformed settings).
- Control operations verify applied state (coordinator.control) with retry; if verification fails raise `HomeAssistantError`.
- API-layer exceptions propagate (SolisCloudControlApiError) and are wrapped as `UpdateFailed` in coordinator update.

Data & State:
- Coordinator data is a mapping `dict[int, str | None]` (CID -> value).
- Entities compute derived numeric/boolean values lazily from coordinator data each property access.
- Range logic: dynamic min/max when battery-dependent; fallback to static domain model constants when no data.

Type Hints & Style:
- Use modern union syntax (`A | B`), explicit return types for async methods (`-> None`).
- Avoid extraneous type comments; rely on hints.
- Prefer `list[...]` literal rather than `List[...]`.

Tests:
- Pytest with fixtures for mock coordinator, inverter objects, and config entries.
- Parametrized tests (`@pytest.mark.parametrize`) for value permutations and boundary cases.
- Assertions on logging side-effects are NOT present; focus is on return values & coordinator.control calls.
- Use `assert_awaited_once_with` on async mocks to validate correct control invocation.

## Maintainability Guidelines
- Keep entity classes cohesive: single responsibility (mapping CIDs to HA features & user interactions).
- Favor small helper methods for repeated calculations (e.g., `_calculate_old_value`).
- Backwards compatibility: preserve existing entity keys (notably omit `_v2` suffix for revised implementations).
- Add new entities / features by extending existing patterns instead of refactoring shared logic prematurely.
- Avoid introducing global mutable state.

## Performance Guidelines
- Batch reads (`read_batch`) followed by individual reads for non-batchable CIDs exactly as coordinator currently does; replicate pattern if expanding.
- Avoid unnecessary refreshes; only call `async_request_refresh` after confirmed control changes.
- Keep synchronous CPU work in entities minimal (simple parsing, arithmetic, bit operations only).

## Security Guidelines
- Never log sensitive credentials (API key/token). Current code does not log them—maintain that.
- Redact inverter serial numbers in diagnostics (pattern already present—follow if adding new fields needing redaction).

## Testability Guidelines
- New logic in entities should be testable via direct instantiation with mock coordinator & manipulated `coordinator.data`.
- For retry/backoff logic, expose delays as constants to permit zero-delay override in tests.
- Provide parametrized tests for: valid values, invalid values, None, edge boundaries (min/max/step rounding), parallel battery scaling.

## Documentation Patterns
- Inline comments are sparse; rely on descriptive names instead of verbose docstrings.
- Only add comments where representation or transformation is non-obvious (e.g., bitmask calculations).

## Testing Approach Details
- Maintain high coverage (threshold 98% from pytest addopts). Any new code must include tests to keep coverage above this line.
- Structure: one test module per platform file; group class-focused tests with nested `Test<ClassName>` classes.
- Use fixtures for entity creation; mutate `coordinator.data` within tests.

## Python-Specific Guidelines
- Use standard library only; no new dependencies unless essential and added to `pyproject.toml`.
- Keep line length <= 120 (Ruff config). Honor existing lint rule selections (annotations required except for allowed ignores in custom_components). Add type hints to new public functions and methods.
- Use f-strings sparingly for logging; prefer logger parameterization.

## Version Control / Changelog
- Follow semantic versioning in `project.version`. Bump only when public integration behavior changes (new entities, breaking key changes, or migration steps).
- Add migration logic in `async_migrate_entry` if data schema changes (increment `VERSION` in `config_flow` + update existing entries accordingly).

## Concrete Examples
When adding a new numeric entity:
1. Extend pattern from `number.py`: create subclass of `SolisCloudControlEntity, NumberEntity`.
2. Provide constructor capturing inverter domain object & setting static attrs (`_attr_*`).
3. Implement `native_value` by extracting CID from `coordinator.data` with `safe_get_float_value` if numeric.
4. Implement `async_set_native_value` rounding & converting to string, then invoking `coordinator.control` with logging.
5. Add tests mirroring `TestMaxOutputPower` style (attributes, native_value parametrized, set_native_value rounding).

When adding a switch with old value verification:
1. Mirror `AllowExportSwitch` deriving `old_value` in helper method.
2. Use `_LOGGER.info("Turn on '%s' (old_value: %s)", self.name, old_value)` style.
3. In tests, set `coordinator.data` initial state and assert control call parameters exactly.

## Prohibited / Avoid
- Introducing patterns not present (e.g., dependency injection frameworks, dataclass usage for entities, excessive inheritance hierarchies).
- Direct API calls from entities (must go through coordinator).
- Raising exceptions for recoverable parse errors—log warning and return `None`.
- Adding `_v2` suffixes to existing entity keys that intentionally preserved backwards compatibility.

## Adding New Files
- Place new platform entity logic in existing platform file when closely related; create a new file only if it represents a distinct platform or large cohesive feature.
- If adding new domain model constructs, prefer `inverters/` or `domain/` directories based on scope (device capability vs. generic value object/bitfield logic).

## Logging Consistency Checklist (apply before committing new code)
- [ ] `_LOGGER` defined at top.
- [ ] Parameterized logging (no f-strings inside log method unless dynamic formatting cannot be parameterized).
- [ ] `debug` only for verbose internal state; `info` for user actions; `warning` for anomalies.

## Test Checklist for New Entity
- [ ] Attribute tests (min/max/step/unit/options pattern).
- [ ] native_value tests (valid, invalid, None).
- [ ] Set/turn action tests (control invocation, rounding, old_value logic if applicable).
- [ ] Edge cases (parallel battery scaling, bitmask composition, dynamic min/max boundaries).

## General Best Practices
- Prefer explicit over implicit, mirroring current code clarity.
- Keep functions short; if a method grows beyond roughly existing method lengths, consider refactoring.
- Prioritize consistency with this integration over external style guides when conflicting.

## Project-Specific Guidance Summary
- Single integration domain `solis_cloud_control`—maintain domain constant reuse.
- All numeric / text / switch / select entities derive availability solely from coordinator data via base entity logic augmented as needed.
- Use value object methods (like `StorageMode`, `ChargeDischargeSettings`) for parsing & serialization—extend them rather than duplicating parsing logic in entities.

By following only the patterns documented above and avoiding external assumptions, generated code will integrate seamlessly with the existing project.
