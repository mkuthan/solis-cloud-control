from dataclasses import dataclass, field
from typing import ClassVar

from custom_components.solis_cloud_control.utils.safe_converters import (
    safe_convert_power_to_watts,
    safe_get_float_value,
)


@dataclass(frozen=True)
class InverterInfo:
    ENERGY_STORAGE_CONTROL_DISABLED: ClassVar[str] = "0"
    TOU_V2_MODE: ClassVar[str] = "43605"  # 0xAA55
    MAX_EXPORT_POWER_DEFAULT: ClassVar[float] = 1_000_000
    MAX_EXPORT_POWER_STEP_DEFAULT: ClassVar[float] = 100
    MAX_EXPORT_POWER_SCALE_DEFAULT: ClassVar[float] = 1.0
    POWER_LIMIT_DEFAULT: ClassVar[float] = 110.0
    PARALLEL_INVERTER_COUNT_DEFAULT: ClassVar[int] = 1
    PARALLEL_BATTERY_COUNT_DEFAULT: ClassVar[int] = 1

    serial_number: str
    model: str | None
    version: str | None
    machine: str | None
    energy_storage_control: str | None
    smart_support: str | None
    generator_support: str | None
    collector_model: str | None
    power: str | None
    power_unit: str | None
    parallel_number: str | None
    parallel_battery: str | None
    tou_v2_mode: str | None = None

    @property
    def is_string_inverter(self) -> bool:
        return (
            self.energy_storage_control is not None
            and self.energy_storage_control == self.ENERGY_STORAGE_CONTROL_DISABLED
        )

    @property
    def is_tou_v2_enabled(self) -> bool:
        return self.tou_v2_mode is not None and self.tou_v2_mode == self.TOU_V2_MODE

    @property
    def max_export_power(self) -> float:
        power = safe_convert_power_to_watts(self.power, self.power_unit)
        if power is not None:
            return power * self.parallel_inverter_count
        else:
            return self.MAX_EXPORT_POWER_DEFAULT

    @property
    def max_export_power_scale(self) -> float:
        if self.model and self.model.lower() in ["3315", "3331", "5305"]:
            return 0.01
        else:
            return self.MAX_EXPORT_POWER_SCALE_DEFAULT

    @property
    def parallel_inverter_count(self) -> int:
        parallel_inverter_count = safe_get_float_value(self.parallel_number)
        if parallel_inverter_count is None or not parallel_inverter_count.is_integer() or parallel_inverter_count < 1:
            return self.PARALLEL_INVERTER_COUNT_DEFAULT
        else:
            return int(parallel_inverter_count)

    @property
    def parallel_battery_count(self) -> int:
        parallel_battery_count = safe_get_float_value(self.parallel_battery)
        if parallel_battery_count is None or not parallel_battery_count.is_integer() or parallel_battery_count < 0:
            return self.PARALLEL_BATTERY_COUNT_DEFAULT
        else:
            return int(parallel_battery_count) + 1


@dataclass(frozen=True)
class InverterOnOff:
    on_cid: int = 52
    off_cid: int = 54
    on_value: str = "190"
    off_value: str = "222"

    def is_valid_value(self, value: str | None) -> bool:
        return value in (self.on_value, self.off_value)


@dataclass(frozen=True)
class InverterStorageMode:
    cid: int = 636


@dataclass(frozen=True)
class InverterChargeDischargeSettings:
    SLOTS_COUNT: ClassVar[int] = 3

    cid: int = 103
    current_min_value: float = 0
    current_max_value: float = 1_000
    current_step: float = 1


@dataclass(frozen=True)
class InverterChargeDischargeSlot:
    switch_cid: int
    time_cid: int
    current_cid: int
    soc_cid: int
    current_min_value: float = 0
    current_max_value: float = 1_000
    current_step: float = 1
    soc_min_value: float = 0
    soc_max_value: float = 100
    soc_step: float = 1

    @property
    def all_cids(self) -> list[int]:
        return [
            self.switch_cid,
            self.time_cid,
            self.current_cid,
            self.soc_cid,
        ]


@dataclass(frozen=True)
class InverterChargeDischargeSlots:
    SLOTS_COUNT: ClassVar[int] = 6

    charge_slot1: InverterChargeDischargeSlot = field(
        default_factory=lambda: InverterChargeDischargeSlot(
            switch_cid=5916,
            time_cid=5946,
            current_cid=5948,
            soc_cid=5928,
        )
    )

    charge_slot2: InverterChargeDischargeSlot = field(
        default_factory=lambda: InverterChargeDischargeSlot(
            switch_cid=5917,
            time_cid=5949,
            current_cid=5951,
            soc_cid=5929,
        )
    )

    charge_slot3: InverterChargeDischargeSlot = field(
        default_factory=lambda: InverterChargeDischargeSlot(
            switch_cid=5918,
            time_cid=5952,
            current_cid=5954,
            soc_cid=5930,
        )
    )
    charge_slot4: InverterChargeDischargeSlot = field(
        default_factory=lambda: InverterChargeDischargeSlot(
            switch_cid=5919,
            time_cid=5955,
            current_cid=5957,
            soc_cid=5931,
        )
    )
    charge_slot5: InverterChargeDischargeSlot = field(
        default_factory=lambda: InverterChargeDischargeSlot(
            switch_cid=5920,
            time_cid=5958,
            current_cid=5960,
            soc_cid=5932,
        )
    )
    charge_slot6: InverterChargeDischargeSlot = field(
        default_factory=lambda: InverterChargeDischargeSlot(
            switch_cid=5921,
            time_cid=5961,
            current_cid=5963,
            soc_cid=5933,
        )
    )

    discharge_slot1: InverterChargeDischargeSlot = field(
        default_factory=lambda: InverterChargeDischargeSlot(
            switch_cid=5922,
            time_cid=5964,
            current_cid=5967,
            soc_cid=5965,
        )
    )

    discharge_slot2: InverterChargeDischargeSlot = field(
        default_factory=lambda: InverterChargeDischargeSlot(
            switch_cid=5923,
            time_cid=5968,
            current_cid=5971,
            soc_cid=5969,
        )
    )
    discharge_slot3: InverterChargeDischargeSlot = field(
        default_factory=lambda: InverterChargeDischargeSlot(
            switch_cid=5924,
            time_cid=5972,
            current_cid=5975,
            soc_cid=5973,
        )
    )
    discharge_slot4: InverterChargeDischargeSlot = field(
        default_factory=lambda: InverterChargeDischargeSlot(
            switch_cid=5925,
            time_cid=5976,
            current_cid=5979,
            soc_cid=5977,
        )
    )
    discharge_slot5: InverterChargeDischargeSlot = field(
        default_factory=lambda: InverterChargeDischargeSlot(
            switch_cid=5926,
            time_cid=5980,
            current_cid=5983,
            soc_cid=5981,
        )
    )
    discharge_slot6: InverterChargeDischargeSlot = field(
        default_factory=lambda: InverterChargeDischargeSlot(
            switch_cid=5927,
            time_cid=5987,
            current_cid=5986,
            soc_cid=5984,
        )
    )

    bit_charge_slot1: int = 0
    bit_charge_slot2: int = 1
    bit_charge_slot3: int = 2
    bit_charge_slot4: int = 3
    bit_charge_slot5: int = 4
    bit_charge_slot6: int = 5
    bit_discharge_slot1: int = 6
    bit_discharge_slot2: int = 7
    bit_discharge_slot3: int = 8
    bit_discharge_slot4: int = 9
    bit_discharge_slot5: int = 10
    bit_discharge_slot6: int = 11

    @property
    def all_cids(self) -> list[int]:
        cids = []

        for slot in [
            self.charge_slot1,
            self.charge_slot2,
            self.charge_slot3,
            self.charge_slot4,
            self.charge_slot5,
            self.charge_slot6,
            self.discharge_slot1,
            self.discharge_slot2,
            self.discharge_slot3,
            self.discharge_slot4,
            self.discharge_slot5,
            self.discharge_slot6,
        ]:
            cids.extend(slot.all_cids)
        return cids

    def get_charge_slot(self, slot_number: int) -> InverterChargeDischargeSlot | None:
        if slot_number == 1:
            return self.charge_slot1
        elif slot_number == 2:
            return self.charge_slot2
        elif slot_number == 3:
            return self.charge_slot3
        elif slot_number == 4:
            return self.charge_slot4
        elif slot_number == 5:
            return self.charge_slot5
        elif slot_number == 6:
            return self.charge_slot6
        else:
            return None

    def get_discharge_slot(self, slot_number: int) -> InverterChargeDischargeSlot | None:
        if slot_number == 1:
            return self.discharge_slot1
        elif slot_number == 2:
            return self.discharge_slot2
        elif slot_number == 3:
            return self.discharge_slot3
        elif slot_number == 4:
            return self.discharge_slot4
        elif slot_number == 5:
            return self.discharge_slot5
        elif slot_number == 6:
            return self.discharge_slot6
        else:
            return None


@dataclass(frozen=True)
class InverterMaxOutputPower:
    cid: int = 376


@dataclass(frozen=True)
class InverterMaxExportPower:
    cid: int = 499
    min_value: float = 0
    max_value: float = InverterInfo.MAX_EXPORT_POWER_DEFAULT
    step: float = InverterInfo.MAX_EXPORT_POWER_STEP_DEFAULT
    scale: float = InverterInfo.MAX_EXPORT_POWER_SCALE_DEFAULT


@dataclass(frozen=True)
class InverterPowerLimit:
    cid: int = 15
    min_value: float = 0
    max_value: float = InverterInfo.POWER_LIMIT_DEFAULT


@dataclass(frozen=True)
class InverterAllowExport:
    cid: int = 6962
    on_value: str = "80"
    off_value: str = "88"


@dataclass(frozen=True)
class InverterBatteryReserveSOC:
    cid: int = 157


@dataclass(frozen=True)
class InverterBatteryOverDischargeSOC:
    cid: int = 158


@dataclass(frozen=True)
class InverterBatteryForceChargeSOC:
    cid: int = 160


@dataclass(frozen=True)
class InverterBatteryRecoverySOC:
    cid: int = 7229


@dataclass(frozen=True)
class InverterBatteryMaxChargeSOC:
    cid: int = 7963


@dataclass(frozen=True)
class InverterBatteryMaxChargeCurrent:
    cid: int = 7224
    parallel_battery_count: int = InverterInfo.PARALLEL_BATTERY_COUNT_DEFAULT


@dataclass(frozen=True)
class InverterBatteryMaxDischargeCurrent:
    cid: int = 7226
    parallel_battery_count: int = InverterInfo.PARALLEL_BATTERY_COUNT_DEFAULT


@dataclass(frozen=True)
class Inverter:
    info: InverterInfo
    on_off: InverterOnOff | None = None
    storage_mode: InverterStorageMode | None = None
    charge_discharge_settings: InverterChargeDischargeSettings | None = None
    charge_discharge_slots: InverterChargeDischargeSlots | None = None
    max_output_power: InverterMaxOutputPower | None = None
    max_export_power: InverterMaxExportPower | None = None
    power_limit: InverterPowerLimit | None = None
    allow_export: InverterAllowExport | None = None
    battery_reserve_soc: InverterBatteryReserveSOC | None = None
    battery_over_discharge_soc: InverterBatteryOverDischargeSOC | None = None
    battery_force_charge_soc: InverterBatteryForceChargeSOC | None = None
    battery_recovery_soc: InverterBatteryRecoverySOC | None = None
    battery_max_charge_soc: InverterBatteryMaxChargeSOC | None = None
    battery_max_charge_current: InverterBatteryMaxChargeCurrent | None = None
    battery_max_discharge_current: InverterBatteryMaxDischargeCurrent | None = None

    @property
    def read_batch_cids(self) -> list[int]:
        cids: list[int] = []

        if self.on_off:
            cids.append(self.on_off.on_cid)
            cids.append(self.on_off.off_cid)
        if self.storage_mode:
            cids.append(self.storage_mode.cid)
        if self.charge_discharge_slots:
            cids.extend(self.charge_discharge_slots.all_cids)
        if self.max_output_power:
            cids.append(self.max_output_power.cid)
        if self.max_export_power:
            cids.append(self.max_export_power.cid)
        if self.power_limit:
            cids.append(self.power_limit.cid)
        if self.allow_export:
            cids.append(self.allow_export.cid)
        if self.battery_reserve_soc:
            cids.append(self.battery_reserve_soc.cid)
        if self.battery_over_discharge_soc:
            cids.append(self.battery_over_discharge_soc.cid)
        if self.battery_force_charge_soc:
            cids.append(self.battery_force_charge_soc.cid)
        if self.battery_recovery_soc:
            cids.append(self.battery_recovery_soc.cid)
        if self.battery_max_charge_soc:
            cids.append(self.battery_max_charge_soc.cid)
        if self.battery_max_charge_current:
            cids.append(self.battery_max_charge_current.cid)
        if self.battery_max_discharge_current:
            cids.append(self.battery_max_discharge_current.cid)

        return cids

    @property
    def read_cids(self) -> list[int]:
        cids = []

        if self.charge_discharge_settings:
            cids.append(self.charge_discharge_settings.cid)

        return cids

    @property
    def all_cids(self) -> list[int]:
        return [*self.read_batch_cids, *self.read_cids]
