import logging
from datetime import datetime

from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CID_CHARGE_SLOT1_TIME, CID_DISCHARGE_SLOT1_TIME
from .coordinator import SolisCloudControlCoordinator
from .entity import SolisCloudControlEntity

_LOGGER = logging.getLogger(__name__)

_TEXT_LEGHT = len("HH:MM-HH:MM")
_TEXT_PATTERN = r"^([01]\d|2[0-3]):([0-5]\d)-([01]\d|2[0-3]):([0-5]\d)$"


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            TimeSlotText(
                coordinator=coordinator,
                entity_description=TextEntityDescription(
                    key="slot1_charge_time",
                    name="Slot1 Charge Time",
                    icon="mdi:timer-plus-outline",
                ),
                cid=CID_CHARGE_SLOT1_TIME,
            ),
            TimeSlotText(
                coordinator=coordinator,
                entity_description=TextEntityDescription(
                    key="slot1_discharge_time",
                    name="Slot1 Discharge Time",
                    icon="mdi:timer-minus-outline",
                ),
                cid=CID_DISCHARGE_SLOT1_TIME,
            ),
        ]
    )


class TimeSlotText(SolisCloudControlEntity, TextEntity):
    def __init__(
        self, coordinator: SolisCloudControlCoordinator, entity_description: TextEntityDescription, cid: int
    ) -> None:
        super().__init__(coordinator, entity_description, cid)
        self._attr_native_min = _TEXT_LEGHT
        self._attr_native_max = _TEXT_LEGHT
        self._attr_pattern = _TEXT_PATTERN

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data:
            return None

        value = self.coordinator.data.get(self.cid)

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
        await self.coordinator.control(self.cid, value)

    def _validate_time_range(self, value: str) -> bool:
        if len(value) != 11 or value.count("-") != 1:
            return False

        try:
            from_str, to_str = value.split("-")
            from_time = datetime.strptime(from_str, "%H:%M")
            to_time = datetime.strptime(to_str, "%H:%M")
            return to_time >= from_time
        except ValueError:
            return False
