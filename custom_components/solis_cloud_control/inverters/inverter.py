from dataclasses import dataclass, field


@dataclass
class InverterInfo:
    serial_number: str
    model: str
    version: str
    machine: str
    power: float | None


@dataclass
class InverterStorageMode:
    cid: int = 636
    mode_self_use: str = "Self-Use"
    mode_feed_in_priority: str = "Feed-In Priority"
    mode_off_grid: str = "Off-Grid"
    bit_self_use: int = 0
    bit_off_grid: int = 2
    bit_backup_mode: int = 4
    bit_grid_charging: int = 5
    bit_feed_in_priority: int = 6


@dataclass
class InverterChargeDischargeSettings:
    cid: int = 103


@dataclass
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


@dataclass
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


@dataclass
class InverterMaxExportPower:
    cid: int = 499
    min_value: float = 0
    max_value: float = 1_000_000
    step: float = 1
    scale: float = 1


@dataclass
class InverterBatteryReserveSOC:
    cid: int = 157


@dataclass
class InverterBatteryOverDischargeSOC:
    cid: int = 158


@dataclass
class InverterBatteryForceChargeSOC:
    cid: int = 160


@dataclass
class InverterBatteryRecoverySOC:
    cid: int = 7229


@dataclass
class InverterBatteryMaxChargeSOC:
    cid: int = 7963


@dataclass
class InverterBatteryMaxChargeCurrent:
    cid: int = 7224


@dataclass
class InverterBatteryMaxDischargeCurrent:
    cid: int = 7226


@dataclass
class Inverter:
    info: InverterInfo
    storage_mode: InverterStorageMode = field(default_factory=InverterStorageMode)
    charge_discharge_settings: InverterChargeDischargeSettings = field(default_factory=InverterChargeDischargeSettings)
    charge_discharge_slots: InverterChargeDischargeSlots = field(default_factory=InverterChargeDischargeSlots)
    max_export_power: InverterMaxExportPower = field(default_factory=InverterMaxExportPower)
    battery_reserve_soc: InverterBatteryReserveSOC = field(default_factory=InverterBatteryReserveSOC)
    battery_over_discharge_soc: InverterBatteryOverDischargeSOC = field(default_factory=InverterBatteryOverDischargeSOC)
    battery_force_charge_soc: InverterBatteryForceChargeSOC = field(default_factory=InverterBatteryForceChargeSOC)
    battery_recovery_soc: InverterBatteryRecoverySOC = field(default_factory=InverterBatteryRecoverySOC)
    battery_max_charge_soc: InverterBatteryMaxChargeSOC = field(default_factory=InverterBatteryMaxChargeSOC)
    battery_max_charge_current: InverterBatteryMaxChargeCurrent = field(default_factory=InverterBatteryMaxChargeCurrent)
    battery_max_discharge_current: InverterBatteryMaxDischargeCurrent = field(
        default_factory=InverterBatteryMaxDischargeCurrent
    )

    @property
    def all_cids(self) -> list[int]:
        return [
            self.storage_mode.cid,
            self.charge_discharge_settings.cid,
            *self.charge_discharge_slots.all_cids,
            self.max_export_power.cid,
            self.battery_reserve_soc.cid,
            self.battery_over_discharge_soc.cid,
            self.battery_force_charge_soc.cid,
            self.battery_recovery_soc.cid,
            self.battery_max_charge_soc.cid,
            self.battery_max_charge_current.cid,
            self.battery_max_discharge_current.cid,
        ]
