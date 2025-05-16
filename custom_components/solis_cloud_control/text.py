import logging
from datetime import datetime

from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry
from custom_components.solis_cloud_control.inverters.inverter import (
    InverterChargeDischargeSettings,
    InverterChargeDischargeSlot,
)

from .coordinator import SolisCloudControlCoordinator
from .entity import SolisCloudControlEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: SolisCloudControlConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    inverter = entry.runtime_data.inverter
    coordinator = entry.runtime_data.coordinator

    entities = []

    if inverter.charge_discharge_settings is not None:
        entities.append(
            ChargeDischargeSettingsText(
                coordinator=coordinator,
                entity_description=TextEntityDescription(
                    key="charge_discharge_settings",
                    name="Charge Discharge Settings",
                    icon="mdi:timer-outline",
                ),
                charge_discharge_settings=inverter.charge_discharge_settings,
            )
        )

    slots = inverter.charge_discharge_slots

    if slots is not None:
        for i in range(1, slots.SLOTS_COUNT + 1):
            entities.append(
                TimeSlotText(
                    coordinator=coordinator,
                    entity_description=TextEntityDescription(
                        key=f"slot{i}_charge_time",
                        name=f"Slot{i} Charge Time",
                        icon="mdi:timer-plus-outline",
                    ),
                    charge_discharge_slot=slots.get_charge_slot(i),
                )
            )
            entities.append(
                TimeSlotText(
                    coordinator=coordinator,
                    entity_description=TextEntityDescription(
                        key=f"slot{i}_discharge_time",
                        name=f"Slot{i} Discharge Time",
                        icon="mdi:timer-minus-outline",
                    ),
                    charge_discharge_slot=slots.get_discharge_slot(i),
                )
            )

    async_add_entities(entities)


class ChargeDischargeSettingsText(SolisCloudControlEntity, TextEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: TextEntityDescription,
        charge_discharge_settings: InverterChargeDischargeSettings,
    ) -> None:
        super().__init__(coordinator, entity_description, charge_discharge_settings.cid)

        self.charge_discharge_settings = charge_discharge_settings

    @property
    def native_value(self) -> str | None:
        value = self.coordinator.data.get(self.charge_discharge_settings.cid)
        return value

    @property
    def extra_state_attributes(self) -> dict[str, str | int]:
        value = self.coordinator.data.get(self.charge_discharge_settings.cid)

        attributes = {}

        if value is None:
            return attributes

        values = value.split(",")
        if len(values) == 18:
            for i in range(1, self.charge_discharge_settings.SLOTS_COUNT + 1):
                base_idx = (i - 1) * 6
                slot_attributes = self._create_attributes_for_slot(values, base_idx, i)
                attributes.update(slot_attributes)

        return attributes

    async def async_set_value(self, value: str) -> None:
        if not self._validate_settings(value):
            raise HomeAssistantError(f"Invalid '{self.name}': {value}")

        _LOGGER.info("Setting '%s' to %s", self.name, value)
        await self.coordinator.control(self.charge_discharge_settings.cid, value)

    def _create_attributes_for_slot(self, values: list[str], base_idx: int, slot_number: int) -> dict[str, str]:
        attributes = {}

        charge_current = values[base_idx]
        attributes[f"slot{slot_number}_charge_current"] = f"{charge_current}"

        discharge_current = values[base_idx + 1]
        attributes[f"slot{slot_number}_discharge_current"] = f"{discharge_current}"

        charge_start = values[base_idx + 2]
        charge_end = values[base_idx + 3]
        attributes[f"slot{slot_number}_charge_time"] = f"{charge_start}-{charge_end}"

        discharge_start = values[base_idx + 4]
        discharge_end = values[base_idx + 5]
        attributes[f"slot{slot_number}_discharge_time"] = f"{discharge_start}-{discharge_end}"

        return attributes

    def _validate_settings(self, value: str) -> bool:
        values = value.split(",")
        if len(values) != 18:
            return False

        try:
            for i in range(0, len(values), 6):
                int(values[i])  # charge_current
                int(values[i + 1])  # discharge_current
                datetime.strptime(values[i + 2], "%H:%M")  # charge_start
                datetime.strptime(values[i + 3], "%H:%M")  # charge_end
                datetime.strptime(values[i + 4], "%H:%M")  # discharge_start
                datetime.strptime(values[i + 5], "%H:%M")  # discharge_end
            return True
        except ValueError:
            return False


class TimeSlotText(SolisCloudControlEntity, TextEntity):
    _TEXT_LENGTH = len("HH:MM-HH:MM")
    _TEXT_PATTERN = r"^([01]\d|2[0-3]):([0-5]\d)-([01]\d|2[0-3]):([0-5]\d)$"

    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: TextEntityDescription,
        charge_discharge_slot: InverterChargeDischargeSlot,
    ) -> None:
        super().__init__(coordinator, entity_description, charge_discharge_slot.time_cid)
        self._attr_native_min = self._TEXT_LENGTH
        self._attr_native_max = self._TEXT_LENGTH
        self._attr_pattern = self._TEXT_PATTERN

        self.charge_discharge_slot = charge_discharge_slot

    @property
    def native_value(self) -> str | None:
        value = self.coordinator.data.get(self.charge_discharge_slot.time_cid)

        if value is None:
            return None

        if not self._validate_time_range(value):
            _LOGGER.warning("Invalid '%s': %s", self.name, value)
            return None

        return value

    async def async_set_value(self, value: str) -> None:
        if not self._validate_time_range(value):
            raise HomeAssistantError(f"Invalid '{self.name}': {value}")

        _LOGGER.info("Setting '%s' to %s", self.name, value)
        await self.coordinator.control(self.charge_discharge_slot.time_cid, value)

    def _validate_time_range(self, value: str) -> bool:
        if len(value) != self._TEXT_LENGTH or value.count("-") != 1:
            return False

        try:
            from_str, to_str = value.split("-")
            from_time = datetime.strptime(from_str, "%H:%M")
            to_time = datetime.strptime(to_str, "%H:%M")
            return to_time >= from_time
        except ValueError:
            return False
