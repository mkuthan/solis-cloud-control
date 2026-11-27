from dataclasses import replace
from typing import TYPE_CHECKING

import pytest

from custom_components.solis_cloud_control.api.solis_api_error import SolisCloudControlApiError
from custom_components.solis_cloud_control.inverters.inverter import (
    Inverter,
    InverterAllowExport,
    InverterBatteryForceChargeSOC,
    InverterBatteryMaxChargeCurrent,
    InverterBatteryMaxChargeSOC,
    InverterBatteryMaxDischargeCurrent,
    InverterBatteryOverDischargeSOC,
    InverterBatteryRecoverySOC,
    InverterBatteryReserveSOC,
    InverterChargeDischargeSettings,
    InverterChargeDischargeSlots,
    InverterExportCalibration,
    InverterGridPeakShaving,
    InverterGridPeakShavingPower,
    InverterInfo,
    InverterMaxExportPower,
    InverterMaxOutputPower,
    InverterMpptScanInterval,
    InverterMpptScanning,
    InverterOnOff,
    InverterPeakShavingBaselineSOC,
    InverterPeakShavingMaxUsableGridPower,
    InverterPowerLimit,
    InverterRemoteDispatchFailsafe,
    InverterRemoteDispatchFunctions,
    InverterRemoteDispatchMaster,
    InverterRemoteDispatchPowerLimit,
    InverterRemoteDispatchRange,
    InverterStorageMode,
    InverterTime,
)
from custom_components.solis_cloud_control.inverters.inverter_factory import (
    create_inverter,
    create_inverter_info,
)
from tests.helpers import ensure

if TYPE_CHECKING:
    from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_create_inverter_info(mock_api_client: AsyncMock) -> None:
    mock_api_client.inverter_details.return_value = {
        "model": "any model",
        "version": "any version",
        "machine": "any machine",
        "energyStorageControl": "1",  # Tou V2 mode is enabled
        "smartSupport": "any smart support",
        "generatorSupport": "any generator support",
        "collectorModel": "any collector model",
        "power": "any power",
        "powerStr": "any power str",
        "parallelNumber": "any parallel number",
        "parallelBattery": "any parallel battery",
    }

    mock_api_client.read.return_value = "any tou v2 mode"
    mock_api_client.read_registers.return_value = [0, 0]

    inverter_sn = "any serial number"
    result = await create_inverter_info(mock_api_client, inverter_sn)

    max_retry_time_seconds = 60
    mock_api_client.inverter_details.assert_awaited_once_with(inverter_sn, max_retry_time_seconds)
    mock_api_client.read.assert_awaited_once_with(inverter_sn, 6798, max_retry_time_seconds)
    mock_api_client.read_registers.assert_awaited_once_with(inverter_sn, 34502, "04", 2, max_retry_time_seconds)

    assert result.serial_number == inverter_sn
    assert result.model == "any model"
    assert result.version == "any version"
    assert result.machine == "any machine"
    assert result.energy_storage_control == "1"
    assert result.smart_support == "any smart support"
    assert result.generator_support == "any generator support"
    assert result.collector_model == "any collector model"
    assert result.power == "any power"
    assert result.power_unit == "any power str"
    assert result.parallel_number == "any parallel number"
    assert result.parallel_battery == "any parallel battery"
    assert result.tou_v2_mode == "any tou v2 mode"
    assert result.remote_dispatch == [0, 0]


@pytest.mark.asyncio
async def test_create_inverter_info_missing_fields(mock_api_client: AsyncMock) -> None:
    mock_api_client.inverter_details.return_value = {}
    mock_api_client.read.return_value = None
    inverter_sn = "any serial number"

    result = await create_inverter_info(mock_api_client, inverter_sn)

    assert result.serial_number == inverter_sn
    assert result.model is None
    assert result.version is None
    assert result.machine is None
    assert result.energy_storage_control is None
    assert result.smart_support is None
    assert result.generator_support is None
    assert result.collector_model is None
    assert result.power is None
    assert result.power_unit is None
    assert result.tou_v2_mode is None


@pytest.mark.asyncio
async def test_create_inverter_info_tou_v2_read_error(mock_api_client: AsyncMock) -> None:
    mock_api_client.inverter_details.return_value = {"energyStorageControl": "1"}
    mock_api_client.read.side_effect = SolisCloudControlApiError("any error")
    inverter_sn = "any serial number"

    with pytest.raises(SolisCloudControlApiError):
        await create_inverter_info(mock_api_client, inverter_sn)


@pytest.mark.asyncio
async def test_create_inverter_info_dispatch_registers_read_error(mock_api_client: AsyncMock) -> None:
    mock_api_client.inverter_details.return_value = {"energyStorageControl": "1"}
    mock_api_client.read_registers.side_effect = SolisCloudControlApiError("any error")
    inverter_sn = "any serial number"

    with pytest.raises(SolisCloudControlApiError):
        await create_inverter_info(mock_api_client, inverter_sn)


@pytest.mark.asyncio
async def test_create_inverter_info_string_inverter(mock_api_client: AsyncMock) -> None:
    mock_api_client.inverter_details.return_value = {
        "energyStorageControl": "0",
    }
    inverter_sn = "any serial number"

    result = await create_inverter_info(mock_api_client, inverter_sn)

    assert result.serial_number == inverter_sn
    assert result.energy_storage_control == "0"
    assert result.tou_v2_mode is None
    assert result.remote_dispatch is None

    mock_api_client.read.assert_not_called()
    mock_api_client.read_registers.assert_not_called()


def test_create_string_inverter(any_inverter_info: InverterInfo) -> None:
    inverter_info = replace(any_inverter_info, energy_storage_control="0")
    result = create_inverter(inverter_info)

    expected = Inverter(
        info=inverter_info,
        on_off=InverterOnOff(on_cid=48, off_cid=53),
        time=InverterTime(cid=18),
        power_limit=InverterPowerLimit(),
    )

    assert result == expected


def test_create_hybrid_inverter(any_inverter_info: InverterInfo) -> None:
    inverter_info = replace(any_inverter_info, energy_storage_control="1", remote_dispatch=[0, 0])
    result = create_inverter(inverter_info)

    expected = Inverter(
        info=inverter_info,
        on_off=InverterOnOff(),
        time=InverterTime(),
        storage_mode=InverterStorageMode(),
        charge_discharge_slots=None,
        charge_discharge_settings=InverterChargeDischargeSettings(),
        max_output_power=InverterMaxOutputPower(),
        max_export_power=InverterMaxExportPower(),
        export_calibration=InverterExportCalibration(),
        allow_export=InverterAllowExport(),
        battery_reserve_soc=InverterBatteryReserveSOC(),
        battery_over_discharge_soc=InverterBatteryOverDischargeSOC(),
        battery_force_charge_soc=InverterBatteryForceChargeSOC(),
        battery_recovery_soc=InverterBatteryRecoverySOC(),
        battery_max_charge_soc=InverterBatteryMaxChargeSOC(),
        battery_max_charge_current=InverterBatteryMaxChargeCurrent(),
        battery_max_discharge_current=InverterBatteryMaxDischargeCurrent(),
        mppt_scan_interval=InverterMpptScanInterval(),
        mppt_scanning=InverterMpptScanning(),
        peak_shaving_max_usable_grid_power=InverterPeakShavingMaxUsableGridPower(),
        peak_shaving_baseline_soc=InverterPeakShavingBaselineSOC(),
        grid_peak_shaving=InverterGridPeakShaving(),
        grid_peak_shaving_power=InverterGridPeakShavingPower(),
        remote_dispatch_failsafe=None,
        remote_dispatch_realtime=None,
        remote_dispatch_periods=None,
    )

    assert result == expected


def test_create_hybrid_inverter_tou_v2_enabled(any_inverter_info: InverterInfo) -> None:
    inverter_info = replace(any_inverter_info, energy_storage_control="1", tou_v2_mode=InverterInfo.TOU_V2_MODE)
    result = create_inverter(inverter_info)

    assert result.charge_discharge_slots == InverterChargeDischargeSlots()
    assert result.charge_discharge_settings is None


def test_create_hybrid_inverter_dispatch_mode_enabled(any_inverter_info: InverterInfo) -> None:
    inverter_info = replace(any_inverter_info, energy_storage_control="1", remote_dispatch=[0xAA55, 3])
    result = create_inverter(inverter_info)

    assert result.remote_dispatch_master == InverterRemoteDispatchMaster()
    assert result.remote_dispatch_failsafe == InverterRemoteDispatchFailsafe()
    assert result.remote_dispatch_import_limit == InverterRemoteDispatchPowerLimit()
    assert result.remote_dispatch_export_limit == InverterRemoteDispatchPowerLimit()
    assert result.remote_dispatch_realtime is not None
    config = result.remote_dispatch_realtime.config
    assert config is not None
    assert config.power == InverterRemoteDispatchRange(-1_000_000, 1_000_000, 10)
    assert config.soc == InverterRemoteDispatchRange(0, 100, 1)
    assert config.reserve_soc == InverterRemoteDispatchRange(0, 100, 1)
    assert config.pv_limit == InverterRemoteDispatchRange(0, 100, 0.01)
    assert config.functions == InverterRemoteDispatchFunctions(
        battery_reserve=True,
        disable_discharge=True,
        demand_control=True,
        pv_limit=True,
    )
    assert result.remote_dispatch_periods is not None
    assert result.remote_dispatch_periods.config is config
    assert [period.number for period in result.remote_dispatch_periods.periods] == [1, 2, 3, 4, 5, 6]


@pytest.mark.parametrize(
    ("version", "has_reserve", "has_pv"),
    [(1, False, False), (2, True, False), (3, True, True)],
)
def test_create_hybrid_inverter_dispatch_config(
    any_inverter_info: InverterInfo, version: int, has_reserve: bool, has_pv: bool
) -> None:
    inverter_info = replace(
        any_inverter_info,
        energy_storage_control="1",
        remote_dispatch=[0xAA55, version],
        power="10",
        power_unit="kW",
        parallel_number="1",
    )
    result = create_inverter(inverter_info)

    assert result.remote_dispatch_realtime is not None
    config = result.remote_dispatch_realtime.config
    assert config is not None
    assert config.power == InverterRemoteDispatchRange(-10_000, 10_000, 10)
    assert (config.reserve_soc is not None) is has_reserve
    assert (config.pv_limit is not None) is has_pv
    assert config.functions.battery_reserve is has_reserve
    assert config.functions.pv_limit is has_pv


@pytest.mark.parametrize("remote_dispatch", [[0, 0], [0, 3], None])
def test_create_hybrid_inverter_dispatch_disabled(
    any_inverter_info: InverterInfo, remote_dispatch: list[int] | None
) -> None:
    inverter_info = replace(any_inverter_info, energy_storage_control="1", remote_dispatch=remote_dispatch)
    result = create_inverter(inverter_info)

    assert result.remote_dispatch_master is None
    assert result.remote_dispatch_failsafe is None
    assert result.remote_dispatch_import_limit is None
    assert result.remote_dispatch_export_limit is None
    assert result.remote_dispatch_realtime is None
    assert result.remote_dispatch_periods is None


def test_create_hybrid_inverter_dispatch_unknown_version(any_inverter_info: InverterInfo) -> None:
    inverter_info = replace(any_inverter_info, energy_storage_control="1", remote_dispatch=[0xAA55, 4])
    result = create_inverter(inverter_info)

    assert result.remote_dispatch_master is None
    assert result.remote_dispatch_failsafe is None
    assert result.remote_dispatch_import_limit is None
    assert result.remote_dispatch_export_limit is None
    assert result.remote_dispatch_realtime is not None
    assert result.remote_dispatch_realtime.config is None
    assert result.remote_dispatch_periods is not None
    assert result.remote_dispatch_periods.config is None


def test_create_hybrid_inverter_max_export_power(any_inverter_info: InverterInfo) -> None:
    inverter_info = replace(
        any_inverter_info, energy_storage_control="1", power="10", power_unit="kW", parallel_number="2.0"
    )
    result = create_inverter(inverter_info)

    assert ensure(result.max_export_power).max_value == 2 * 10_000


@pytest.mark.parametrize("model", ["3105", "3173", "3315", "3316", "3331", "3332", "4104", "5305"])
def test_create_hybrid_inverter_max_export_power_scale(any_inverter_info: InverterInfo, model: str) -> None:
    inverter_info = replace(any_inverter_info, energy_storage_control="1", model=model)
    result = create_inverter(inverter_info)

    assert ensure(result.max_export_power).scale == 0.01


def test_create_hybrid_inverter_battery_max_current(any_inverter_info: InverterInfo) -> None:
    inverter_info = replace(any_inverter_info, energy_storage_control="1", parallel_battery="2.0")
    result = create_inverter(inverter_info)

    assert ensure(result.battery_max_charge_current).parallel_battery_count == 3
    assert ensure(result.battery_max_discharge_current).parallel_battery_count == 3
