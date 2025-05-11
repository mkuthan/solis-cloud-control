from unittest.mock import AsyncMock, patch

import pytest

from custom_components.solis_cloud_control.inverters.default_hybrid_inverter import (
    create_default_hybrid_inverter,
)
from custom_components.solis_cloud_control.inverters.inverter import (
    InverterBatteryForceChargeSOC,
    InverterBatteryMaxChargeCurrent,
    InverterBatteryMaxChargeSOC,
    InverterBatteryMaxDischargeCurrent,
    InverterBatteryOverDischargeSOC,
    InverterBatteryRecoverySOC,
    InverterBatteryReserveSOC,
    InverterChargeDischargeSettings,
    InverterChargeDischargeSlots,
    InverterMaxExportPower,
    InverterStorageMode,
)


@pytest.mark.asyncio
async def test_create_default_hybrid_inverter_slots_enabled(mock_api_client, any_inverter_info) -> None:
    with patch(
        "custom_components.solis_cloud_control.inverters.default_hybrid_inverter.charge_discharge_mode_slots_enabled",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_slots_enabled:
        inverter = await create_default_hybrid_inverter(mock_api_client, any_inverter_info)

        mock_slots_enabled.assert_called_once_with(mock_api_client, any_inverter_info.serial_number)
        assert inverter.info == any_inverter_info
        assert isinstance(inverter.storage_mode, InverterStorageMode)
        assert isinstance(inverter.charge_discharge_slots, InverterChargeDischargeSlots)
        assert inverter.charge_discharge_settings is None
        assert isinstance(inverter.max_export_power, InverterMaxExportPower)
        assert isinstance(inverter.battery_reserve_soc, InverterBatteryReserveSOC)
        assert isinstance(inverter.battery_over_discharge_soc, InverterBatteryOverDischargeSOC)
        assert isinstance(inverter.battery_force_charge_soc, InverterBatteryForceChargeSOC)
        assert isinstance(inverter.battery_recovery_soc, InverterBatteryRecoverySOC)
        assert isinstance(inverter.battery_max_charge_soc, InverterBatteryMaxChargeSOC)
        assert isinstance(inverter.battery_max_charge_current, InverterBatteryMaxChargeCurrent)
        assert isinstance(inverter.battery_max_discharge_current, InverterBatteryMaxDischargeCurrent)


@pytest.mark.asyncio
async def test_create_default_hybrid_inverter_slots_disabled(mock_api_client, any_inverter_info) -> None:
    with patch(
        "custom_components.solis_cloud_control.inverters.default_hybrid_inverter.charge_discharge_mode_slots_enabled",
        new_callable=AsyncMock,
        return_value=False,
    ) as mock_slots_enabled:
        inverter = await create_default_hybrid_inverter(mock_api_client, any_inverter_info)

        mock_slots_enabled.assert_called_once_with(mock_api_client, any_inverter_info.serial_number)
        assert inverter.info == any_inverter_info
        assert isinstance(inverter.storage_mode, InverterStorageMode)
        assert inverter.charge_discharge_slots is None
        assert isinstance(inverter.charge_discharge_settings, InverterChargeDischargeSettings)
        assert isinstance(inverter.max_export_power, InverterMaxExportPower)
        assert isinstance(inverter.battery_reserve_soc, InverterBatteryReserveSOC)
        assert isinstance(inverter.battery_over_discharge_soc, InverterBatteryOverDischargeSOC)
        assert isinstance(inverter.battery_force_charge_soc, InverterBatteryForceChargeSOC)
        assert isinstance(inverter.battery_recovery_soc, InverterBatteryRecoverySOC)
        assert isinstance(inverter.battery_max_charge_soc, InverterBatteryMaxChargeSOC)
        assert isinstance(inverter.battery_max_charge_current, InverterBatteryMaxChargeCurrent)
        assert isinstance(inverter.battery_max_discharge_current, InverterBatteryMaxDischargeCurrent)
