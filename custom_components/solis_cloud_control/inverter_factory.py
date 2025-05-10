from custom_components.solis_cloud_control.api import SolisCloudControlApiClient
from custom_components.solis_cloud_control.inverter import (
    Inverter,
    InverterBatteryForceChargeSOC,
    InverterBatteryMaxChargeSOC,
    InverterBatteryOverDischargeSOC,
    InverterBatteryRecoverySOC,
    InverterBatteryReserveSOC,
    InverterChargeDischargeSettings,
    InverterChargeDischargeSlots,
    InverterInfo,
    InverterMaxChargingCurrent,
    InverterMaxDischargingCurrent,
    InverterMaxExportPower,
    InverterStorageMode,
)

_CHARGE_DISCHARGE_MODE_CID = 6798
_CHARGE_DISCHARGE_MODE_USING_SLOTS = 43605  # 0xAA55


async def create_inverter_info(api_client: SolisCloudControlApiClient, inverter_sn: str) -> InverterInfo:
    inverter_details = await api_client.inverter_details(inverter_sn)

    model = str(inverter_details.get("model", "Unknown"))
    version = str(inverter_details.get("version", "Unknown"))
    machine = str(inverter_details.get("machine", "Unknown"))

    return InverterInfo(
        serial_number=inverter_sn,
        model=model,
        version=version,
        machine=machine,
    )


async def create_inverter(api_client: SolisCloudControlApiClient, inverter_info: InverterInfo) -> Inverter:
    if inverter_info.model == "3331":
        return await _create_3331(api_client, inverter_info)

    #
    # Extension point for other models
    #
    # elif model == "XXXX":
    #     return await _create_xxxx(api_client, inverter_sn, details)

    else:
        return Inverter(inverter_info)


async def _create_3331(api_client: SolisCloudControlApiClient, inverter_info: InverterInfo) -> Inverter:
    inverter = Inverter(
        info=inverter_info,
        storage_mode=InverterStorageMode(),
        max_export_power=InverterMaxExportPower(max_value=13_200, step=100, scale=0.01),
        max_charging_current=InverterMaxChargingCurrent(),
        max_discharging_current=InverterMaxDischargingCurrent(),
        battery_reserve_soc=InverterBatteryReserveSOC(),
        battery_over_discharge_soc=InverterBatteryOverDischargeSOC(),
        battery_force_charge_soc=InverterBatteryForceChargeSOC(),
        battery_recovery_soc=InverterBatteryRecoverySOC(),
        battery_max_charge_soc=InverterBatteryMaxChargeSOC(),
    )

    charge_discharge_mode = await api_client.read(inverter_info.serial_number, _CHARGE_DISCHARGE_MODE_CID)

    if charge_discharge_mode == str(_CHARGE_DISCHARGE_MODE_USING_SLOTS):
        inverter.charge_discharge_slots = InverterChargeDischargeSlots()
    else:
        inverter.charge_discharge_settings = InverterChargeDischargeSettings()

    return inverter
