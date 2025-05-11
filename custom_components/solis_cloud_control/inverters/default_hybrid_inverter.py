from custom_components.solis_cloud_control.api import SolisCloudControlApiClient
from custom_components.solis_cloud_control.inverters.inverter import (
    Inverter,
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
    InverterStorageMode,
)
from custom_components.solis_cloud_control.inverters.inverter_utils import charge_discharge_mode_slots_enabled


async def create_default_hybrid_inverter(
    api_client: SolisCloudControlApiClient, inverter_info: InverterInfo
) -> Inverter:
    inverter = Inverter(
        info=inverter_info,
        storage_mode=InverterStorageMode(),
        max_export_power=InverterMaxExportPower(),
        battery_reserve_soc=InverterBatteryReserveSOC(),
        battery_over_discharge_soc=InverterBatteryOverDischargeSOC(),
        battery_force_charge_soc=InverterBatteryForceChargeSOC(),
        battery_recovery_soc=InverterBatteryRecoverySOC(),
        battery_max_charge_soc=InverterBatteryMaxChargeSOC(),
        battery_max_charge_current=InverterBatteryMaxChargeCurrent(),
        battery_max_discharge_current=InverterBatteryMaxDischargeCurrent(),
    )

    if await charge_discharge_mode_slots_enabled(api_client, inverter_info.serial_number):
        inverter.charge_discharge_slots = InverterChargeDischargeSlots()
    else:
        inverter.charge_discharge_settings = InverterChargeDischargeSettings()

    return inverter
