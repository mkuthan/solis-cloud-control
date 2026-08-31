---
name: add-inverter-entity
description: Add or change a Home Assistant entity that maps a Solis CID to a number, switch, select, text, sensor, or datetime platform. Use when adding a new inverter control, changing an entity's range, unit, or options, or wiring a new inverter capability into inverter_factory.
---

# Adding or changing an inverter entity

This task has a fixed blast radius of seven files. Step 7 fails silently until the very end of a full test
run, which is why this skill exists. Work in this order.

## Work order

1. **Capability — `custom_components/solis_cloud_control/inverters/inverter.py`**
   Add or adjust the capability dataclass (e.g. `InverterMpptScanning`) carrying the CID and any bounds,
   scale, or options. Add the corresponding field to the `Inverter` holder. Follow the existing dataclasses
   exactly — defaults for CIDs go in the dataclass, not in the factory.

2. **Wiring — `custom_components/solis_cloud_control/inverters/inverter_factory.py`**
   Add it to the correct branch: `_create_string_inverter` or `_create_hybrid_inverter`. Getting this wrong is
   the most common mistake — string inverters expose a deliberately small subset. If a capability depends on
   inverter details, compute the value from `inverter_info` in the factory (see `max_export_power` for the
   pattern).

3. **Entity — the platform file** (`number.py`, `switch.py`, `select.py`, `text.py`, `sensor.py`,
   `datetime.py`)
   Add the entity class, then append it in `async_setup_entry` inside an `if inverter.<capability> is not
   None:` guard. Display name goes in the inline `name=` of the `*EntityDescription` — **not** in
   `translations/en.json`, which is config-flow strings only.

4. **Fixture — `tests/conftest.py`**
   Add the capability to the `any_inverter` fixture. Skipping this makes the factory test pass vacuously.

5. **Factory test — `tests/inverters/test_inverter_factory.py`**
   Assert the capability is present for the inverter kinds that should have it and absent for the others.

6. **Entity test — `tests/test_<platform>.py`**
   Mirror the existing test classes. Parametrize boundary, `None`, invalid, and rounding cases. Use the
   `mock_coordinator` fixture; assert observable outcomes (returned values, `coordinator.control` calls,
   state), never log text.

7. **Entity counts — `tests/test_init.py`**
   Bump the hard-coded counts. Update **both** blocks: `platform_counts` and, if the entity is disabled by
   default, `platform_disabled_counts`.

8. **Docs — `README.md`**
   Update the feature list if the entity is user-visible.

## Proof of success

`mise run check` green — including the 98% *branch* coverage gate. A partial run
(`uv run pytest --cov-fail-under=0 tests/test_switch.py`) is for iterating only; it does not mean done.
