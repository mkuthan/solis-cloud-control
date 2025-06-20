from dataclasses import dataclass, field, replace

from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient
from custom_components.solis_cloud_control.utils.safe_converters import safe_convert_power_to_watts


@dataclass(frozen=True)
class InverterInfo:
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

    @property
    def power_watts(self) -> float | None:
        return safe_convert_power_to_watts(self.power, self.power_unit)

    @property
    def is_string_inverter(self) -> bool:
        return self.energy_storage_control is not None and self.energy_storage_control == "0"


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
    SLOTS_COUNT: int = 3

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
    SLOTS_COUNT: int = 6

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
    max_value: float = 1_000_000
    step: float = 1
    scale: float = 1


@dataclass(frozen=True)
class InverterPowerLimit:
    cid: int = 15
    min_value: float = 0
    max_value: float = 110


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


@dataclass(frozen=True)
class InverterBatteryMaxDischargeCurrent:
    cid: int = 7226


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
    battery_reserve_soc: InverterBatteryReserveSOC | None = None
    battery_over_discharge_soc: InverterBatteryOverDischargeSOC | None = None
    battery_force_charge_soc: InverterBatteryForceChargeSOC | None = None
    battery_recovery_soc: InverterBatteryRecoverySOC | None = None
    battery_max_charge_soc: InverterBatteryMaxChargeSOC | None = None
    battery_max_charge_current: InverterBatteryMaxChargeCurrent | None = None
    battery_max_discharge_current: InverterBatteryMaxDischargeCurrent | None = None

    @staticmethod
    async def create_string_inverter(
        inverter_info: InverterInfo,
        api_client: SolisCloudControlApiClient,  # noqa: ARG004
    ) -> "Inverter":
        return Inverter(
            info=inverter_info,
            on_off=InverterOnOff(on_cid=48, off_cid=53),
            power_limit=InverterPowerLimit(),
        )

    @staticmethod
    async def create_hybrid_inverter(
        inverter_info: InverterInfo,
        api_client: SolisCloudControlApiClient,
    ) -> "Inverter":
        inverter = Inverter(
            info=inverter_info,
            on_off=InverterOnOff(on_cid=52, off_cid=54),
            storage_mode=InverterStorageMode(),
            max_output_power=InverterMaxOutputPower(),
            max_export_power=InverterMaxExportPower(),
            battery_reserve_soc=InverterBatteryReserveSOC(),
            battery_over_discharge_soc=InverterBatteryOverDischargeSOC(),
            battery_force_charge_soc=InverterBatteryForceChargeSOC(),
            battery_recovery_soc=InverterBatteryRecoverySOC(),
            battery_max_charge_soc=InverterBatteryMaxChargeSOC(),
            battery_max_charge_current=InverterBatteryMaxChargeCurrent(),
            battery_max_discharge_current=InverterBatteryMaxDischargeCurrent(),
        )

        tou_v2_mode = await api_client.read(inverter_info.serial_number, 6798)

        if tou_v2_mode is not None and tou_v2_mode == "43605":  # 0xAA55
            inverter = replace(inverter, charge_discharge_slots=InverterChargeDischargeSlots())
        else:
            inverter = replace(inverter, charge_discharge_settings=InverterChargeDischargeSettings())

        return inverter

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
