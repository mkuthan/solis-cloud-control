import logging

from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import InvalidEntityFormatError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.utils import validate_time_range

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

        return self.coordinator.data.get(self.cid)

    async def async_set_value(self, value: str) -> None:
        if not validate_time_range(value):
            raise InvalidEntityFormatError(f"Invalid time range: {value}")

        _LOGGER.info(
            "Setting time slot to %s for inverter %s",
            value,
            self.coordinator.inverter_sn,
        )

        await self.coordinator.api_client.control(self.coordinator.inverter_sn, self.cid, value)
        await self.coordinator.async_request_refresh()
