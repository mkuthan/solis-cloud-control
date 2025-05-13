import logging

from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry
from custom_components.solis_cloud_control.inverters.inverter import (
    InverterChargeDischargeSettings,
    InverterChargeDischargeSlot,
)
from custom_components.solis_cloud_control.time_utils import validate_time_range

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

    for i in range(1, slots.SLOT_COUNT + 1):
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

        if not validate_time_range(value):
            _LOGGER.warning("Invalid '%s': %s", self.name, value)
            return None

        return value

    async def async_set_value(self, value: str) -> None:
        if not validate_time_range(value):
            raise HomeAssistantError(f"Invalid '{self.name}': {value}")

        _LOGGER.info("Setting '%s' to %s", self.name, value)
        await self.coordinator.control(self.charge_discharge_slot.time_cid, value)
