from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CID_CHARGE_SLOT1_TIME, CID_DISCHARGE_SLOT1_TIME
from .coordinator import SolisCloudControlCoordinator
from .entity import SolisCloudControlEntity

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
                cid=CID_CHARGE_SLOT1_TIME,
                entity_description=TextEntityDescription(
                    key="slot1_charge_time",
                    name="Slot1 Charge Time",
                    icon="mdi:timer-plus-outline",
                ),
            ),
            TimeSlotText(
                coordinator=coordinator,
                cid=CID_DISCHARGE_SLOT1_TIME,
                entity_description=TextEntityDescription(
                    key="slot1_discharge_time",
                    name="Slot1 Discharge Time",
                    icon="mdi:timer-minus-outline",
                ),
            ),
        ]
    )


class TimeSlotText(SolisCloudControlEntity, TextEntity):
    def __init__(
        self, coordinator: SolisCloudControlCoordinator, cid: int, entity_description: TextEntityDescription
    ) -> None:
        super().__init__(coordinator, cid)
        self.entity_description = entity_description
        self._attr_native_min = _TEXT_LEGHT
        self._attr_native_max = _TEXT_LEGHT
        self._attr_pattern = _TEXT_PATTERN

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data:
            return None

        return self.coordinator.data.get(self.cid)

    async def async_set_value(self, value: str) -> None:
        await self.coordinator.api_client.control(self.coordinator.inverter_sn, self.cid, value)
        await self.coordinator.async_request_refresh()
