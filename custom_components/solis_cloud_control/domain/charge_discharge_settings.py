from abc import ABC, abstractmethod

from custom_components.solis_cloud_control.utils.safe_converters import safe_get_float_value


class ChargeDischargeSettings(ABC):
    @staticmethod
    def create(data: str | None) -> "ChargeDischargeSettings | None":
        if not data:
            return None

        fields = data.split(",")
        fields_length = len(fields)

        if fields_length == 18:
            return ChargeDischargeSettingsVariant1(fields)
        elif fields_length == 12:
            return ChargeDischargeSettingsVariant2(fields)
        else:
            return None

    @abstractmethod
    def get_charge_power(self, slot: int) -> float | None:
        pass

    @abstractmethod
    def get_discharge_power(self, slot: int) -> float | None:
        pass

    @abstractmethod
    def get_charge_time_slot(self, slot: int) -> str | None:
        pass

    @abstractmethod
    def get_discharge_time_slot(self, slot: int) -> str | None:
        pass

    @abstractmethod
    def set_charge_power(self, slot: int, power: float) -> None:
        pass

    @abstractmethod
    def set_discharge_power(self, slot: int, power: float) -> None:
        pass

    @abstractmethod
    def set_charge_time_slot(self, slot: int, time_slot: str) -> None:
        pass

    @abstractmethod
    def set_discharge_time_slot(self, slot: int, time_slot: str) -> None:
        pass

    @staticmethod
    def _validate_fields_length(fields: list[str], expected_length: int) -> list[str]:
        if len(fields) != expected_length:
            raise ValueError(f"Invalid format, expected {expected_length} fields, got {len(fields)}")
        return fields

    @staticmethod
    def _validate_slot_index(slot: int) -> None:
        if slot < 1 or slot > 3:
            raise ValueError(f"Invalid slot number {slot}, must be between 1 and 3")


class ChargeDischargeSettingsVariant1(ChargeDischargeSettings):
    def __init__(self, fields: list[str]) -> None:
        self._fields = ChargeDischargeSettings._validate_fields_length(fields, 18)

    def get_charge_power(self, slot: int) -> float | None:
        ChargeDischargeSettings._validate_slot_index(slot)

        base_idx = (slot - 1) * 6
        return safe_get_float_value(self._fields[base_idx])

    def get_discharge_power(self, slot: int) -> float | None:
        ChargeDischargeSettings._validate_slot_index(slot)

        base_idx = (slot - 1) * 6
        return safe_get_float_value(self._fields[base_idx + 1])

    def get_charge_time_slot(self, slot: int) -> str | None:
        ChargeDischargeSettings._validate_slot_index(slot)

        base_idx = (slot - 1) * 6

        charge_start = self._fields[base_idx + 2]
        charge_end = self._fields[base_idx + 3]

        return f"{charge_start}-{charge_end}"

    def get_discharge_time_slot(self, slot: int) -> str | None:
        ChargeDischargeSettings._validate_slot_index(slot)

        base_idx = (slot - 1) * 6

        discharge_start = self._fields[base_idx + 4]
        discharge_end = self._fields[base_idx + 5]

        return f"{discharge_start}-{discharge_end}"

    def set_charge_power(self, slot: int, power: float) -> None:
        ChargeDischargeSettings._validate_slot_index(slot)

        base_idx = (slot - 1) * 6
        self._fields[base_idx] = str(power)

    def set_discharge_power(self, slot: int, power: float) -> None:
        ChargeDischargeSettings._validate_slot_index(slot)

        base_idx = (slot - 1) * 6
        self._fields[base_idx + 1] = str(power)

    def set_charge_time_slot(self, slot: int, time_slot: str) -> None:
        ChargeDischargeSettings._validate_slot_index(slot)

        start_time, end_time = time_slot.split("-", 1)
        base_idx = (slot - 1) * 6
        self._fields[base_idx + 2] = start_time
        self._fields[base_idx + 3] = end_time

    def set_discharge_time_slot(self, slot: int, time_slot: str) -> None:
        ChargeDischargeSettings._validate_slot_index(slot)

        start_time, end_time = time_slot.split("-", 1)
        base_idx = (slot - 1) * 6
        self._fields[base_idx + 4] = start_time
        self._fields[base_idx + 5] = end_time

    def __str__(self) -> str:
        return ",".join(self._fields)


class ChargeDischargeSettingsVariant2(ChargeDischargeSettings):
    def __init__(self, fields: list[str]) -> None:
        self._fields = ChargeDischargeSettings._validate_fields_length(fields, 12)

    def get_charge_power(self, slot: int) -> float | None:
        ChargeDischargeSettings._validate_slot_index(slot)

        base_idx = (slot - 1) * 4
        return safe_get_float_value(self._fields[base_idx])

    def get_discharge_power(self, slot: int) -> float | None:
        ChargeDischargeSettings._validate_slot_index(slot)

        base_idx = (slot - 1) * 4
        return safe_get_float_value(self._fields[base_idx + 1])

    def get_charge_time_slot(self, slot: int) -> str | None:
        ChargeDischargeSettings._validate_slot_index(slot)

        base_idx = (slot - 1) * 4
        return self._fields[base_idx + 2]

    def get_discharge_time_slot(self, slot: int) -> str | None:
        ChargeDischargeSettings._validate_slot_index(slot)

        base_idx = (slot - 1) * 4
        return self._fields[base_idx + 3]

    def set_charge_power(self, slot: int, power: float) -> None:
        ChargeDischargeSettings._validate_slot_index(slot)

        base_idx = (slot - 1) * 4
        self._fields[base_idx] = str(power)

    def set_discharge_power(self, slot: int, power: float) -> None:
        ChargeDischargeSettings._validate_slot_index(slot)

        base_idx = (slot - 1) * 4
        self._fields[base_idx + 1] = str(power)

    def set_charge_time_slot(self, slot: int, time_slot: str) -> None:
        ChargeDischargeSettings._validate_slot_index(slot)

        base_idx = (slot - 1) * 4
        self._fields[base_idx + 2] = time_slot

    def set_discharge_time_slot(self, slot: int, time_slot: str) -> None:
        ChargeDischargeSettings._validate_slot_index(slot)

        base_idx = (slot - 1) * 4
        self._fields[base_idx + 3] = time_slot

    def __str__(self) -> str:
        return ",".join(self._fields)
