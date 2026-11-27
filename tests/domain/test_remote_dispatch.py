from datetime import time
from typing import cast

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
    RemoteDispatch,
)


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








def test_limit_getters(holding: list[int]) -> None:
    dispatch = RemoteDispatch.create([0xAA55, 3, 0], holding)

    assert dispatch.settings is not None
    assert dispatch.settings.import_limit_enabled is True
    assert dispatch.settings.import_limit_watts is None
    assert dispatch.settings.export_limit_enabled is False
    assert dispatch.settings.export_limit_watts == 0








def test_dispatch_functions_api() -> None:
    functions = DispatchFunctions(pv_shutdown=False, disable_discharge=True)

    assert functions.value_of(DispatchFunction.PV_SHUTDOWN) is False
    assert functions.value_of(DispatchFunction.DISABLE_DISCHARGE) is True

    updated = functions.with_function(DispatchFunction.PV_SHUTDOWN, True)

    assert updated.pv_shutdown is True
    with pytest.raises(ValueError, match="on or off"):
        functions.with_function(DispatchFunction.PV_SHUTDOWN, cast("bool", 1))
