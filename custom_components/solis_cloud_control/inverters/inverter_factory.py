from dataclasses import replace

from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient
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


async def create_inverter_info(api_client: SolisCloudControlApiClient, inverter_sn: str) -> InverterInfo:
    inverter_details = await api_client.inverter_details(inverter_sn)

    inverter_info = InverterInfo(
        serial_number=inverter_sn,
        model=_get_inverter_detail(inverter_details, "model"),
        version=_get_inverter_detail(inverter_details, "version"),
        machine=_get_inverter_detail(inverter_details, "machine"),
        energy_storage_control=_get_inverter_detail(inverter_details, "energyStorageControl"),
        smart_support=_get_inverter_detail(inverter_details, "smartSupport"),
        generator_support=_get_inverter_detail(inverter_details, "generatorSupport"),
        collector_model=_get_inverter_detail(inverter_details, "collectorModel"),
        power=_get_inverter_detail(inverter_details, "power"),
        power_unit=_get_inverter_detail(inverter_details, "powerStr"),
        parallel_number=_get_inverter_detail(inverter_details, "parallelNumber"),
        parallel_battery=_get_inverter_detail(inverter_details, "parallelBattery"),
        tou_v2_mode=None,
    )

    if not inverter_info.is_string_inverter:
        tou_v2_mode = await api_client.read(inverter_sn, 6798)
        inverter_info = replace(inverter_info, tou_v2_mode=tou_v2_mode)

    return inverter_info


def create_inverter(inverter_info: InverterInfo) -> Inverter:
    if inverter_info.is_string_inverter:
        return _create_string_inverter(inverter_info)
    else:
        return _create_hybrid_inverter(inverter_info)


def _get_inverter_detail(inverter_details: dict[str, any], field: str) -> str | None:
    return str(value) if (value := inverter_details.get(field)) is not None else None


def _create_string_inverter(
    inverter_info: InverterInfo,
) -> Inverter:
    return Inverter(
        info=inverter_info,
        on_off=InverterOnOff(on_cid=48, off_cid=53),
        time=InverterTime(cid=18),
        power_limit=InverterPowerLimit(),
    )


def _create_hybrid_inverter(inverter_info: InverterInfo) -> Inverter:
    if inverter_info.is_tou_v2_enabled:
        charge_discharge_slots = InverterChargeDischargeSlots()
        charge_discharge_settings = None
    else:
        charge_discharge_slots = None
        charge_discharge_settings = InverterChargeDischargeSettings()

    max_export_power = InverterMaxExportPower(
        max_value=inverter_info.max_export_power, scale=inverter_info.max_export_power_scale
    )

    battery_max_charge_current = InverterBatteryMaxChargeCurrent(
        parallel_battery_count=inverter_info.parallel_battery_count
    )

    battery_max_discharge_current = InverterBatteryMaxDischargeCurrent(
        parallel_battery_count=inverter_info.parallel_battery_count
    )

    return Inverter(
        info=inverter_info,
        on_off=InverterOnOff(),
        time=InverterTime(),
        storage_mode=InverterStorageMode(),
        charge_discharge_slots=charge_discharge_slots,
        charge_discharge_settings=charge_discharge_settings,
        max_output_power=InverterMaxOutputPower(),
        max_export_power=max_export_power,
        allow_export=InverterAllowExport(),
        battery_reserve_soc=InverterBatteryReserveSOC(),
        battery_over_discharge_soc=InverterBatteryOverDischargeSOC(),
        battery_force_charge_soc=InverterBatteryForceChargeSOC(),
        battery_recovery_soc=InverterBatteryRecoverySOC(),
        battery_max_charge_soc=InverterBatteryMaxChargeSOC(),
        battery_max_charge_current=battery_max_charge_current,
        battery_max_discharge_current=battery_max_discharge_current,
    )
