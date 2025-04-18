import logging

from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry
from custom_components.solis_cloud_control.time_utils import validate_time_range

from .const import CID_CHARGE_SLOT1_TIME, CID_DISCHARGE_SLOT1_TIME
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
    coordinator = entry.runtime_data.coordinator
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
        value = self.coordinator.data.get(self.cid)

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
        await self.coordinator.control(self.cid, value)
