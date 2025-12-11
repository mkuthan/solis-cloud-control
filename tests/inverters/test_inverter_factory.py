from dataclasses import replace

import pytest

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
    InverterInfo,
    InverterMaxExportPower,
    InverterMaxOutputPower,
    InverterOnOff,
    InverterPowerLimit,
    InverterStorageMode,
    InverterTime,
)
from custom_components.solis_cloud_control.inverters.inverter_factory import (
    create_inverter,
    create_inverter_info,
)


@pytest.mark.asyncio
async def test_create_inverter_info(mock_api_client):
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

    inverter_sn = "any serial number"
    result = await create_inverter_info(mock_api_client, inverter_sn)

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


@pytest.mark.asyncio
async def test_create_inverter_info_missing_fields(mock_api_client):
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
async def test_create_inverter_info_string_inverter(mock_api_client):
    mock_api_client.inverter_details.return_value = {
        "energyStorageControl": "0",
    }
    inverter_sn = "any serial number"

    result = await create_inverter_info(mock_api_client, inverter_sn)

    assert result.serial_number == inverter_sn
    assert result.energy_storage_control == "0"
    assert result.tou_v2_mode is None

    mock_api_client.read.assert_not_called()


def test_create_string_inverter(any_inverter_info):
    inverter_info = replace(any_inverter_info, energy_storage_control="0")
    result = create_inverter(inverter_info)

    expected = Inverter(
        info=inverter_info,
        on_off=InverterOnOff(on_cid=48, off_cid=53),
        time=InverterTime(cid=18),
        power_limit=InverterPowerLimit(),
    )

    assert result == expected


def test_create_hybrid_inverter(any_inverter_info):
    inverter_info = replace(any_inverter_info, energy_storage_control="1")
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
        allow_export=InverterAllowExport(),
        battery_reserve_soc=InverterBatteryReserveSOC(),
        battery_over_discharge_soc=InverterBatteryOverDischargeSOC(),
        battery_force_charge_soc=InverterBatteryForceChargeSOC(),
        battery_recovery_soc=InverterBatteryRecoverySOC(),
        battery_max_charge_soc=InverterBatteryMaxChargeSOC(),
        battery_max_charge_current=InverterBatteryMaxChargeCurrent(),
        battery_max_discharge_current=InverterBatteryMaxDischargeCurrent(),
    )

    assert result == expected


def test_create_hybrid_inverter_tou_v2_enabled(any_inverter_info):
    inverter_info = replace(any_inverter_info, energy_storage_control="1", tou_v2_mode=InverterInfo.TOU_V2_MODE)
    result = create_inverter(inverter_info)

    assert result.charge_discharge_slots == InverterChargeDischargeSlots()
    assert result.charge_discharge_settings is None


def test_create_hybrid_inverter_max_export_power(any_inverter_info):
    inverter_info = replace(
        any_inverter_info, energy_storage_control="1", power="10", power_unit="kW", parallel_number="2.0"
    )
    result = create_inverter(inverter_info)

    assert result.max_export_power.max_value == 2 * 10_000


@pytest.mark.parametrize("model", ["3315", "3331", "5305"])
def test_create_hybrid_inverter_max_export_power_scale(any_inverter_info, model):
    inverter_info = replace(any_inverter_info, energy_storage_control="1", model=model)
    result = create_inverter(inverter_info)

    assert result.max_export_power.scale == 0.01


def test_create_hybrid_inverter_battery_max_current(any_inverter_info):
    inverter_info = replace(any_inverter_info, energy_storage_control="1", parallel_battery="2.0")
    result = create_inverter(inverter_info)

    assert result.battery_max_charge_current.parallel_battery_count == 3
    assert result.battery_max_discharge_current.parallel_battery_count == 3
