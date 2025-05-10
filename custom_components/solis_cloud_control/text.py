import logging

from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry
from custom_components.solis_cloud_control.inverter import InverterChargeDischargeSlot
from custom_components.solis_cloud_control.time_utils import validate_time_range

from .coordinator import SolisCloudControlCoordinator
from .entity import SolisCloudControlEntity

_LOGGER = logging.getLogger(__name__)

_TEXT_LEGHT = len("HH:MM-HH:MM")
_TEXT_PATTERN = r"^([01]\d|2[0-3]):([0-5]\d)-([01]\d|2[0-3]):([0-5]\d)$"


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: SolisCloudControlConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    inverter = entry.runtime_data.inverter
    coordinator = entry.runtime_data.coordinator

    entities = []

    if inverter.charge_discharge_slots is not None:
        entities.append(
            TimeSlotText(
                coordinator=coordinator,
                entity_description=TextEntityDescription(
                    key="slot1_charge_time",
                    name="Slot1 Charge Time",
                    icon="mdi:timer-plus-outline",
                ),
                charge_discharge_slot=inverter.charge_discharge_slots.charge_slot1,
            )
        )
        entities.append(
            TimeSlotText(
                coordinator=coordinator,
                entity_description=TextEntityDescription(
                    key="slot1_discharge_time",
                    name="Slot1 Discharge Time",
                    icon="mdi:timer-minus-outline",
                ),
                charge_discharge_slot=inverter.charge_discharge_slots.discharge_slot1,
            )
        )

    async_add_entities(entities)


class TimeSlotText(SolisCloudControlEntity, TextEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: TextEntityDescription,
        charge_discharge_slot: InverterChargeDischargeSlot,
    ) -> None:
        super().__init__(coordinator, entity_description)
        self._attr_native_min = _TEXT_LEGHT
        self._attr_native_max = _TEXT_LEGHT
        self._attr_pattern = _TEXT_PATTERN

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
