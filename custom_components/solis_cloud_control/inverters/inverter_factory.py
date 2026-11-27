from dataclasses import replace
from typing import TYPE_CHECKING

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
    InverterRemoteDispatchCommand,
    InverterRemoteDispatchCommandConfig,
    InverterRemoteDispatchFailsafe,
    InverterRemoteDispatchFunctions,
    InverterRemoteDispatchMaster,
    InverterRemoteDispatchPeriods,
    InverterRemoteDispatchPowerLimit,
    InverterRemoteDispatchRange,
    InverterStorageMode,
    InverterTime,
)

if TYPE_CHECKING:
    from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient

_MAX_RETRY_TIME_SECONDS = 60


async def create_inverter_info(api_client: SolisCloudControlApiClient, inverter_sn: str) -> InverterInfo:
    inverter_details = await api_client.inverter_details(inverter_sn, _MAX_RETRY_TIME_SECONDS)

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
        tou_v2_mode = await api_client.read(inverter_sn, 6798, _MAX_RETRY_TIME_SECONDS)
        inverter_info = replace(inverter_info, tou_v2_mode=tou_v2_mode)

    if not inverter_info.is_string_inverter:
        remote_dispatch = await api_client.read_registers(inverter_sn, 34502, "04", 2, _MAX_RETRY_TIME_SECONDS)
        inverter_info = replace(inverter_info, remote_dispatch=remote_dispatch)

    return inverter_info


def create_inverter(inverter_info: InverterInfo) -> Inverter:
    if inverter_info.is_string_inverter:
        return _create_string_inverter(inverter_info)
    else:
        return _create_hybrid_inverter(inverter_info)


def _get_inverter_detail(inverter_details: dict, field: str) -> str | None:
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

    known_remote_dispatch = inverter_info.is_remote_dispatch_enabled and inverter_info.remote_dispatch_version in (
        1,
        2,
        3,
    )
    command_config = _create_remote_dispatch_command_config(inverter_info) if known_remote_dispatch else None

    if inverter_info.is_remote_dispatch_enabled:
        remote_dispatch_realtime = InverterRemoteDispatchCommand(config=command_config)
        remote_dispatch_periods = InverterRemoteDispatchPeriods(config=command_config)
    else:
        remote_dispatch_realtime = None
        remote_dispatch_periods = None

    remote_dispatch_master = InverterRemoteDispatchMaster() if known_remote_dispatch else None
    remote_dispatch_failsafe = InverterRemoteDispatchFailsafe() if known_remote_dispatch else None
    remote_dispatch_import_limit = InverterRemoteDispatchPowerLimit() if known_remote_dispatch else None
    remote_dispatch_export_limit = InverterRemoteDispatchPowerLimit() if known_remote_dispatch else None

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
        export_calibration=InverterExportCalibration(),
        allow_export=InverterAllowExport(),
        battery_reserve_soc=InverterBatteryReserveSOC(),
        battery_over_discharge_soc=InverterBatteryOverDischargeSOC(),
        battery_force_charge_soc=InverterBatteryForceChargeSOC(),
        battery_recovery_soc=InverterBatteryRecoverySOC(),
        battery_max_charge_soc=InverterBatteryMaxChargeSOC(),
        battery_max_charge_current=battery_max_charge_current,
        battery_max_discharge_current=battery_max_discharge_current,
        mppt_scan_interval=InverterMpptScanInterval(),
        mppt_scanning=InverterMpptScanning(),
        peak_shaving_max_usable_grid_power=InverterPeakShavingMaxUsableGridPower(),
        peak_shaving_baseline_soc=InverterPeakShavingBaselineSOC(),
        grid_peak_shaving=InverterGridPeakShaving(),
        grid_peak_shaving_power=InverterGridPeakShavingPower(),
        remote_dispatch_master=remote_dispatch_master,
        remote_dispatch_failsafe=remote_dispatch_failsafe,
        remote_dispatch_import_limit=remote_dispatch_import_limit,
        remote_dispatch_export_limit=remote_dispatch_export_limit,
        remote_dispatch_realtime=remote_dispatch_realtime,
        remote_dispatch_periods=remote_dispatch_periods,
    )


def _create_remote_dispatch_command_config(inverter_info: InverterInfo) -> InverterRemoteDispatchCommandConfig:
    version = inverter_info.remote_dispatch_version
    max_power = int(inverter_info.max_export_power)
    return InverterRemoteDispatchCommandConfig(
        power=InverterRemoteDispatchRange(-max_power, max_power, 10),
        soc=InverterRemoteDispatchRange(0, 100, 1),
        reserve_soc=InverterRemoteDispatchRange(0, 100, 1) if version >= 2 else None,
        pv_limit=InverterRemoteDispatchRange(0, 100, 0.01) if version == 3 else None,
        functions=InverterRemoteDispatchFunctions(
            battery_reserve=version >= 2,
            disable_discharge=version >= 2,
            demand_control=version >= 2,
            pv_limit=version == 3,
        ),
    )
