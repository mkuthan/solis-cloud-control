from dataclasses import replace
from datetime import time
from typing import TYPE_CHECKING, cast

import pytest

from custom_components.solis_cloud_control.domain.remote_dispatch import (
    HOLDING_COUNT,
    HOLDING_START,
    DispatchCapabilities,
    DispatchCommand,
    DispatchFunction,
    DispatchFunctions,
    DispatchMode,
    DispatchPowerLimit,
    DispatchRunningState,
    RegisterWrite,
    RemoteDispatch,
    apply_writes,
    encode_changes,
    encode_start,
    encode_stop,
)

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.fixture
def holding() -> list[int]:
    settings = [0, 5, 0x8001, -1, 0]
    realtime = [2, -1, -300, 0b10_01_10_01_10_01_10_01, 10, 90, 40, 7564]
    periods = [
        [0, hour << 8 | 15, hour << 8 | 55, 4, 0, 0, 0, 0, 100, 42, 8765, 0xAAAA, 0xBBBB, 0xCCCC]
        for hour in range(1, 7)
    ]
    return [*settings, *realtime, 0xAAAA, 0xBBBB, 0xCCCC, *(word for period in periods for word in period)]


@pytest.mark.parametrize("version", [1, 2, 3])
def test_decode_full_snapshot(holding: list[int], version: int) -> None:
    dispatch = RemoteDispatch.create([-21931, version, 0x0403], holding)
    caps = dispatch.capabilities
    assert caps.supported
    assert caps.version == version
    assert caps.supports_battery_reserve == (version >= 2)
    assert caps.supports_discharge_prohibition == (version >= 2)
    assert caps.supports_demand_control == (version >= 2)
    assert caps.supports_pv_limit == (version >= 3)
    assert (DispatchMode.SELF_CONSUMPTION in caps.supported_modes) == (version >= 2)
    assert (DispatchMode.FEED_IN_PRIORITY in caps.supported_modes) == (version >= 2)
    assert dispatch.status is not None
    assert dispatch.status.state == DispatchRunningState.SCHEDULED
    assert dispatch.status.active_mode == (DispatchMode.GRID_PORT_POWER if version >= 2 else None)

    assert dispatch.settings is not None
    assert dispatch.settings.enabled is False
    assert dispatch.settings.failsafe_minutes == 5
    assert dispatch.settings.import_limit == DispatchPowerLimit(enabled=True, watts=None)
    assert dispatch.settings.export_limit == DispatchPowerLimit(enabled=False, watts=0)
    assert dispatch.realtime == DispatchCommand(
        mode=DispatchMode.BATTERY_POWER,
        power_w=-3000,
        functions=DispatchFunctions(
            pv_shutdown=False,
            digital_output_closed=True,
            allow_grid_charge=True,
            off_grid_battery_standby=True,
            battery_reserve_enabled=False if version >= 2 else None,
            disable_discharge=True if version >= 2 else None,
            demand_control_enabled=False if version >= 2 else None,
            pv_limit_enabled=True if version >= 3 else None,
        ),
        soc_min_pct=10,
        soc_max_pct=90,
        reserve_soc_pct=40 if version >= 2 else None,
        pv_limit_pct=75.64 if version >= 3 else None,
    )

    assert len(dispatch.periods) == 6
    for number, period in enumerate(dispatch.periods, start=1):
        assert dispatch.period(number) == period
        assert period.enabled is False
        assert period.start == time(number, 15)
        assert period.end == time(number, 55)
        assert period.command.mode == DispatchMode.GRID_PORT_POWER
        assert period.command.power_w == 0
        assert period.command.reserve_soc_pct == (42 if version >= 2 else None)
        assert period.command.pv_limit_pct == (87.65 if version >= 3 else None)


@pytest.mark.parametrize("number", [0, -1, 7])
def test_period_number_validation(holding: list[int], number: int) -> None:
    dispatch = RemoteDispatch.create([0xAA55, 3, 0], holding)
    with pytest.raises(ValueError, match="not available"):
        dispatch.with_period(number, dispatch.period(1))


def test_unrecognized_period_data_does_not_hide_other_periods(holding: list[int]) -> None:
    holding[16:25] = [2, 0x1800, 0x003C, 99, 0, 0, 3, 0, 100]
    dispatch = RemoteDispatch.create([0xAA55, 3, 0xFFFF], holding)
    assert dispatch.status is not None
    assert dispatch.status.state is None
    assert dispatch.status.active_mode is None
    first = dispatch.period(1)
    assert first.enabled is None
    assert first.start is None
    assert first.end is None
    assert first.command.mode is None
    assert first.command.functions.pv_shutdown is None
    assert dispatch.period(2).start == time(2, 15)


@pytest.mark.parametrize(("version", "last_command_offset"), [(1, 9), (2, 10), (3, 11)])
def test_edit_only_period_six(holding: list[int], version: int, last_command_offset: int) -> None:
    holding[92] = 0xFFFF  # Both invalid directives and unsupported pairs must survive unrelated edits.
    before = RemoteDispatch.create([0xAA55, version, 0], holding)
    after = before.with_period(6, replace(before.period(6), start=time(7, 30)))

    expected = holding[86 : 86 + last_command_offset]
    expected[1] = 0x071E
    assert encode_changes(before, after, holding) == [RegisterWrite(44186, tuple(expected))]
    assert before.period(6).start == time(6, 15)
    assert before.periods[:5] == after.periods[:5]


def test_edit_all_function_switches(holding: list[int]) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)
    assert before.realtime is not None
    after = before.with_realtime(
        replace(
            before.realtime,
            functions=DispatchFunctions(True, False, False, False, True, False, True, False),
            power_w=1230,
        )
    )

    assert encode_changes(before, after, holding) == [
        RegisterWrite(44105, (2, 0, 123, 0b01_10_01_10_01_10_01_10, 10, 90, 40, 7564))
    ]


def test_edit_limits_preserves_unknown_switch_bits(holding: list[int]) -> None:
    before = RemoteDispatch.create([0xAA55, 1, 0], holding)
    assert before.settings is not None
    after = before.with_settings(
        replace(
            before.settings,
            import_limit=DispatchPowerLimit(enabled=False, watts=3500),
            export_limit=DispatchPowerLimit(enabled=True, watts=None),
        )
    )

    assert encode_changes(before, after, holding) == [RegisterWrite(44100, (0, 5, 0x8002, 35, 0xFFFF))]


def test_soc_edit_preserves_adjacent_setpoints(holding: list[int]) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)
    assert before.realtime is not None
    after = before.with_realtime(replace(before.realtime, soc_max_pct=85))
    assert encode_changes(before, after, holding) == [
        RegisterWrite(44105, (2, 0xFFFF, 0xFED4, holding[8], 10, 85, 40, 7564))
    ]


def test_setting_reserve_and_pv_limit_does_not_toggle_their_switches(holding: list[int]) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)
    period = before.period(6)
    command = replace(period.command, reserve_soc_pct=37, pv_limit_pct=12.34)
    after = before.with_period(6, replace(period, command=command))
    assert encode_changes(before, after, holding) == [
        RegisterWrite(44186, (0, 0x060F, 0x0637, 4, 0, 0, 0, 0, 100, 37, 1234))
    ]


@pytest.mark.parametrize(
    ("edit", "message"),
    [
        ({"mode": DispatchMode.SELF_CONSUMPTION}, "Unsupported Remote Dispatch mode"),
        ({"power_w": 111}, "10 W steps"),
        ({"soc_max_pct": 10}, "SOC bounds"),
        ({"reserve_soc_pct": 45}, "Battery reserve requires"),
        ({"pv_limit_pct": 75.01}, "PV limiting requires"),
        ({"functions": DispatchFunctions(True, True, True, True, demand_control_enabled=True)}, "not supported"),
    ],
)
def test_invalid_command_edits(holding: list[int], edit: dict, message: str) -> None:
    before = RemoteDispatch.create([0xAA55, 1, 0], holding)
    assert before.realtime is not None
    after = before.with_realtime(replace(before.realtime, **edit))
    with pytest.raises(ValueError, match=message):
        encode_changes(before, after, holding)


def test_validate_time_edits(holding: list[int]) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)
    after = before.with_period(3, replace(before.period(3), start=time(8, 30, 1)))
    with pytest.raises(ValueError, match="whole minutes"):
        encode_changes(before, after, holding)


def test_power_convenience_constructors() -> None:
    assert DispatchCommand.battery_charge(0) == DispatchCommand.battery_discharge(0)
    assert DispatchCommand.battery_charge(3000).power_w == 3000
    assert DispatchCommand.battery_discharge(3000).power_w == -3000
    with pytest.raises(ValueError, match="non-negative"):
        DispatchCommand.battery_discharge(-3000)


def test_invalid_snapshot_lengths() -> None:
    with pytest.raises(ValueError, match="input registers"):
        RemoteDispatch.create([0xAA55, 1], [])
    with pytest.raises(ValueError, match="holding registers"):
        RemoteDispatch.create([0xAA55, 3, 0], [0] * 99)


@pytest.mark.parametrize(("signature", "version", "expected_version"), [(0, 1, None), (0xAA55, 4, 4)])
def test_create_capability_only_snapshot(signature: int, version: int, expected_version: int | None) -> None:
    dispatch = RemoteDispatch.create([signature, version, 0], [])
    assert dispatch.capabilities.version == expected_version
    assert not dispatch.capabilities.known_version
    assert dispatch.status is None
    assert dispatch.settings is None
    assert dispatch.realtime is None
    assert dispatch.periods == ()


def test_failsafe_edit_writes_full_settings_block(holding: list[int]) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)

    after = before.with_failsafe_minutes(15)

    assert encode_changes(before, after, holding) == [RegisterWrite(HOLDING_START, (0, 15, 0x8001, 0xFFFF, 0))]
    assert before.settings is not None
    assert before.settings.failsafe_minutes == 5


def test_with_failsafe_minutes_requires_settings() -> None:
    dispatch = RemoteDispatch(DispatchCapabilities(False, None))

    with pytest.raises(ValueError, match="settings"):
        dispatch.with_failsafe_minutes(15)


@pytest.mark.parametrize("minutes", [0, -1, 1441, True])
def test_with_failsafe_minutes_validates(holding: list[int], minutes: int) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)

    with pytest.raises(ValueError, match="failsafe"):
        before.with_failsafe_minutes(minutes)


def test_encode_start_writes_full_settings_block(holding: list[int]) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)

    assert encode_start(before, holding) == RegisterWrite(HOLDING_START, (1, 5, 0x8001, 0xFFFF, 0))


def test_encode_stop_writes_full_settings_block(holding: list[int]) -> None:
    holding[0] = 1

    assert encode_stop(holding) == RegisterWrite(HOLDING_START, (0, 5, 0x8001, 0xFFFF, 0))


def test_from_registers_decodes_holding_only(holding: list[int]) -> None:
    registers = {HOLDING_START + offset: word for offset, word in enumerate(holding)}

    dispatch = RemoteDispatch.from_registers(registers, DispatchCapabilities(True, 3))

    assert dispatch is not None
    assert dispatch.status is None
    assert dispatch.settings is not None
    assert dispatch.settings.failsafe_minutes == 5
    assert dispatch.realtime is not None
    assert dispatch.realtime.power_w == -3000
    assert dispatch.period(6).start == time(6, 15)


@pytest.mark.parametrize("capabilities", [DispatchCapabilities(True, 4), DispatchCapabilities(False, None)])
def test_from_registers_requires_known_version(holding: list[int], capabilities: DispatchCapabilities) -> None:
    registers = {HOLDING_START + offset: word for offset, word in enumerate(holding)}

    assert RemoteDispatch.from_registers(registers, capabilities) is None


def test_from_registers_requires_complete_block(holding: list[int]) -> None:
    registers: dict[int, int | None] = {HOLDING_START + offset: word for offset, word in enumerate(holding)}
    registers[HOLDING_START] = None
    capabilities = DispatchCapabilities(True, 3)

    assert RemoteDispatch.from_registers(registers, capabilities) is None

    registers[HOLDING_START] = holding[0]
    registers.pop(HOLDING_START + HOLDING_COUNT - 1)

    assert RemoteDispatch.from_registers(registers, capabilities) is None


def test_apply_writes_updates_only_written_registers(holding: list[int]) -> None:
    registers = {HOLDING_START + offset: word for offset, word in enumerate(holding)}
    write = RegisterWrite(HOLDING_START, (1, 15, 0x8001, 0xFFFF, 0))

    updated = apply_writes(registers, [write])

    assert updated[HOLDING_START] == 1
    assert updated[HOLDING_START + 1] == 15
    assert updated[HOLDING_START + 5] == registers[HOLDING_START + 5]
    assert registers[HOLDING_START] == holding[0]


def test_limit_enabled_edits_write_full_settings_block(holding: list[int]) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)

    import_off = before.with_import_limit_enabled(False)
    export_on = before.with_export_limit_enabled(True)
    export_off = export_on.with_export_limit_enabled(False)

    assert encode_changes(before, import_off, holding) == [RegisterWrite(HOLDING_START, (0, 5, 0x8000, 0xFFFF, 0))]
    assert encode_changes(before, export_on, holding) == [RegisterWrite(HOLDING_START, (0, 5, 0x8003, 0xFFFF, 0))]
    assert encode_changes(export_on, export_off, holding) == [RegisterWrite(HOLDING_START, (0, 5, 0x8001, 0xFFFF, 0))]


def test_limit_watts_edits_write_full_settings_block(holding: list[int]) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)

    after = before.with_import_limit_watts(3500).with_export_limit_watts(1200)

    assert encode_changes(before, after, holding) == [RegisterWrite(HOLDING_START, (0, 5, 0x8001, 35, 12))]


def test_limit_getters(holding: list[int]) -> None:
    dispatch = RemoteDispatch.create([0xAA55, 3, 0], holding)

    assert dispatch.settings is not None
    assert dispatch.settings.import_limit_enabled is True
    assert dispatch.settings.import_limit_watts is None
    assert dispatch.settings.export_limit_enabled is False
    assert dispatch.settings.export_limit_watts == 0


@pytest.mark.parametrize("watts", [-100, 150, 6_553_500, True])
def test_limit_watts_validation(holding: list[int], watts: int) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)

    with pytest.raises(ValueError, match="Power"):
        before.with_import_limit_watts(watts)


@pytest.mark.parametrize("enabled", [0, 1, None])
def test_limit_switch_validation(holding: list[int], enabled: bool) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)

    with pytest.raises(ValueError, match="on or off"):
        before.with_import_limit_enabled(enabled)


@pytest.mark.parametrize(
    "edit",
    [
        lambda dispatch: dispatch.with_import_limit_enabled(True),
        lambda dispatch: dispatch.with_import_limit_watts(100),
        lambda dispatch: dispatch.with_export_limit_enabled(True),
        lambda dispatch: dispatch.with_export_limit_watts(100),
    ],
)
def test_limit_edits_require_settings(edit: Callable[[RemoteDispatch], RemoteDispatch]) -> None:
    dispatch = RemoteDispatch(DispatchCapabilities(False, None))

    with pytest.raises(ValueError, match="settings"):
        edit(dispatch)


def test_dispatch_functions_api() -> None:
    functions = DispatchFunctions(pv_shutdown=False, disable_discharge=True)

    assert functions.value_of(DispatchFunction.PV_SHUTDOWN) is False
    assert functions.value_of(DispatchFunction.DISABLE_DISCHARGE) is True

    updated = functions.with_function(DispatchFunction.PV_SHUTDOWN, True)

    assert updated.pv_shutdown is True
    with pytest.raises(ValueError, match="on or off"):
        functions.with_function(DispatchFunction.PV_SHUTDOWN, cast("bool", 1))


def test_realtime_mode_edit(holding: list[int]) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)

    after = before.with_realtime_mode(DispatchMode.SELF_CONSUMPTION)

    assert encode_changes(before, after, holding) == [
        RegisterWrite(44105, (5, 0xFFFF, 0xFED4, holding[8], 10, 90, 40, 7564))
    ]


def test_realtime_power_edit(holding: list[int]) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)

    after = before.with_realtime_power(1230)

    assert encode_changes(before, after, holding) == [RegisterWrite(44105, (2, 0, 123, holding[8], 10, 90, 40, 7564))]


def test_realtime_soc_reserve_and_pv_edits(holding: list[int]) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)

    after = before.with_realtime_soc_bounds(20, 80).with_realtime_reserve_soc(45).with_realtime_pv_limit(42.5)

    assert encode_changes(before, after, holding) == [
        RegisterWrite(44105, (2, 0xFFFF, 0xFED4, holding[8], 20, 80, 45, 4250))
    ]


def test_realtime_function_edit(holding: list[int]) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)

    after = before.with_realtime_function(DispatchFunction.PV_SHUTDOWN, True)

    assert encode_changes(before, after, holding) == [
        RegisterWrite(44105, (2, 0xFFFF, 0xFED4, 0x999A, 10, 90, 40, 7564))
    ]


@pytest.mark.parametrize(
    ("version", "edit", "message"),
    [
        (1, lambda dispatch: dispatch.with_realtime_reserve_soc(40), "Battery reserve requires"),
        (2, lambda dispatch: dispatch.with_realtime_pv_limit(50), "PV limiting requires"),
        (3, lambda dispatch: dispatch.with_realtime_power(111), "10 W steps"),
        (3, lambda dispatch: dispatch.with_realtime_soc_bounds(50, 40), "SOC bounds"),
        (3, lambda dispatch: dispatch.with_realtime_mode(DispatchMode.GRID_POWER), None),
    ],
)
def test_realtime_edit_validation(
    holding: list[int],
    version: int,
    edit: Callable[[RemoteDispatch], RemoteDispatch],
    message: str | None,
) -> None:
    before = RemoteDispatch.create([0xAA55, version, 0], holding)

    if message is None:
        edit(before)
    else:
        with pytest.raises(ValueError, match=message):
            edit(before)


def test_realtime_function_requires_companion_values(holding: list[int]) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)
    assert before.realtime is not None
    without_reserve = before.with_realtime(replace(before.realtime, reserve_soc_pct=None))
    without_pv = before.with_realtime(replace(before.realtime, pv_limit_pct=None))

    with pytest.raises(ValueError, match="battery reserve SOC"):
        without_reserve.with_realtime_function(DispatchFunction.BATTERY_RESERVE_ENABLED, True)
    with pytest.raises(ValueError, match="PV limit"):
        without_pv.with_realtime_function(DispatchFunction.PV_LIMIT_ENABLED, True)


def test_period_start_edit(holding: list[int]) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)
    expected = holding[16:27]
    expected[1] = 0x021E

    after = before.with_period_start(1, time(2, 30))

    assert encode_changes(before, after, holding) == [RegisterWrite(44116, tuple(expected))]


def test_period_enable_edit(holding: list[int]) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)
    expected = holding[16:27]
    expected[0] = 1

    after = before.with_period_enabled(1, True)

    assert encode_changes(before, after, holding) == [RegisterWrite(44116, tuple(expected))]


def test_period_enable_requires_start_and_end(holding: list[int]) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)
    period = before.period(1)
    without_start = before.with_period(1, replace(period, start=None))

    with pytest.raises(ValueError, match="start and end"):
        without_start.with_period_enabled(1, True)


@pytest.mark.parametrize(
    ("edit", "message"),
    [
        (lambda dispatch: dispatch.with_period_start(1, time(2, 30, 1)), "whole minutes"),
        (lambda dispatch: dispatch.with_period_mode(1, DispatchMode.BATTERY_POWER), None),
    ],
)
def test_period_edit_validation(
    holding: list[int],
    edit: Callable[[RemoteDispatch], RemoteDispatch],
    message: str | None,
) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)

    if message is None:
        edit(before)
    else:
        with pytest.raises(ValueError, match=message):
            edit(before)


def test_period_command_edits(holding: list[int]) -> None:
    before = RemoteDispatch.create([0xAA55, 3, 0], holding)

    after = (
        before.with_period_mode(1, DispatchMode.BATTERY_POWER)
        .with_period_power(1, 1230)
        .with_period_soc_bounds(1, 20, 80)
        .with_period_reserve_soc(1, 45)
        .with_period_pv_limit(1, 42.5)
        .with_period_function(1, DispatchFunction.PV_SHUTDOWN, True)
    )

    assert encode_changes(before, after, holding) == [
        RegisterWrite(44116, (0, 0x010F, 0x0137, 2, 0, 123, 2, 20, 80, 45, 4250))
    ]
