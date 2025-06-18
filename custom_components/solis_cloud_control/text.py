import logging
from typing import Literal

from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry
from custom_components.solis_cloud_control.domain.charge_discharge_settings import ChargeDischargeSettings
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

    charge_discharge_settings = inverter.charge_discharge_settings

    if charge_discharge_settings is not None:
        for i in range(1, charge_discharge_settings.SLOTS_COUNT + 1):
            entities.extend(
                [
                    TimeSlotV1Text(
                        coordinator=coordinator,
                        entity_description=TextEntityDescription(
                            key=f"slot{i}_charge_time_v1",
                            name=f"Slot{i} Charge Time",
                            icon="mdi:timer-plus-outline",
                        ),
                        inverter_charge_discharge_settings=charge_discharge_settings,
                        slot_number=i,
                        slot_type="charge",
                    ),
                    TimeSlotV1Text(
                        coordinator=coordinator,
                        entity_description=TextEntityDescription(
                            key=f"slot{i}_discharge_time_v1",
                            name=f"Slot{i} Discharge Time",
                            icon="mdi:timer-minus-outline",
                        ),
                        inverter_charge_discharge_settings=charge_discharge_settings,
                        slot_number=i,
                        slot_type="discharge",
                    ),
                ]
            )

    charge_discharge_slots = inverter.charge_discharge_slots

    if charge_discharge_slots is not None:
        for i in range(1, charge_discharge_slots.SLOTS_COUNT + 1):
            entities.extend(
                [
                    TimeSlotV2Text(
                        coordinator=coordinator,
                        entity_description=TextEntityDescription(
                            key=f"slot{i}_charge_time",  # don't use _v2 suffix for backwards compatibility
                            name=f"Slot{i} Charge Time",
                            icon="mdi:timer-plus-outline",
                        ),
                        inverter_charge_discharge_slot=charge_discharge_slots.get_charge_slot(i),
                    ),
                    TimeSlotV2Text(
                        coordinator=coordinator,
                        entity_description=TextEntityDescription(
                            key=f"slot{i}_discharge_time",  # don't use _v2 suffix for backwards compatibility
                            name=f"Slot{i} Discharge Time",
                            icon="mdi:timer-minus-outline",
                        ),
                        inverter_charge_discharge_slot=charge_discharge_slots.get_discharge_slot(i),
                    ),
                ]
            )

    async_add_entities(entities)


class TimeSlotV1Text(SolisCloudControlEntity, TextEntity):
    _TEXT_LENGTH = len("HH:MM-HH:MM")
    _TEXT_PATTERN = r"^([01]\d|2[0-3]):([0-5]\d)-([01]\d|2[0-3]):([0-5]\d)$"

    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: TextEntityDescription,
        inverter_charge_discharge_settings: InverterChargeDischargeSettings,
        slot_number: int,
        slot_type: Literal["charge", "discharge"],
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_charge_discharge_settings.cid)
        self._attr_native_min = self._TEXT_LENGTH
        self._attr_native_max = self._TEXT_LENGTH
        self._attr_pattern = self._TEXT_PATTERN

        self.inverter_charge_discharge_settings = inverter_charge_discharge_settings
        self.slot_number = slot_number
        self.slot_type = slot_type

    @property
    def native_value(self) -> str | None:
        current_value = self.coordinator.data.get(self.inverter_charge_discharge_settings.cid)

        charge_discharge_settings = ChargeDischargeSettings.create(current_value)
        if charge_discharge_settings is None:
            _LOGGER.warning("Invalid '%s' settings: '%s'", self.name, current_value)
            return None

        if self.slot_type == "charge":
            time_slot = charge_discharge_settings.get_charge_time_slot(self.slot_number)
        else:
            time_slot = charge_discharge_settings.get_discharge_time_slot(self.slot_number)

        return time_slot

    async def async_set_value(self, value: str) -> None:
        current_value = self.coordinator.data.get(self.inverter_charge_discharge_settings.cid)
        charge_discharge_settings = ChargeDischargeSettings.create(current_value)

        if charge_discharge_settings is None:
            _LOGGER.warning("Invalid '%s' settings: '%s'", self.name, current_value)
            return None

        if self.slot_type == "charge":
            charge_discharge_settings.set_charge_time_slot(self.slot_number, value)
        else:
            charge_discharge_settings.set_discharge_time_slot(self.slot_number, value)

        value_str = charge_discharge_settings.to_value()

        _LOGGER.info("Set '%s' to %s (value: %s)", self.name, value, value_str)
        await self.coordinator.control(self.inverter_charge_discharge_settings.cid, value_str)


class TimeSlotV2Text(SolisCloudControlEntity, TextEntity):
    _TEXT_LENGTH = len("HH:MM-HH:MM")
    _TEXT_PATTERN = r"^([01]\d|2[0-3]):([0-5]\d)-([01]\d|2[0-3]):([0-5]\d)$"

    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: TextEntityDescription,
        inverter_charge_discharge_slot: InverterChargeDischargeSlot,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_charge_discharge_slot.time_cid)
        self._attr_native_min = self._TEXT_LENGTH
        self._attr_native_max = self._TEXT_LENGTH
        self._attr_pattern = self._TEXT_PATTERN

        self.inverter_charge_discharge_slot = inverter_charge_discharge_slot

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get(self.inverter_charge_discharge_slot.time_cid)

    async def async_set_value(self, value: str) -> None:
        _LOGGER.info("Set '%s' to %s", self.name, value)
        await self.coordinator.control(self.inverter_charge_discharge_slot.time_cid, value)
