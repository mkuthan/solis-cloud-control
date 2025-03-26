from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.const import (
    CID_STORAGE_MODE,
)
from custom_components.solis_cloud_control.coordinator import SolisCloudControlConfigEntry, SolisCloudControlCoordinator
from custom_components.solis_cloud_control.entity import SolisCloudControlEntity

_ENTITY_DESCRIPTIONS = (
    SelectEntityDescription(
        key="storage_mode",
        name="Storage Mode",
        icon="mdi:solar-power",
    ),
)

_MODE_SELF_USE = "Self-Use"
_MODE_FEED_IN_PRIORITY = "Feed-In Priority"

_BIT_SELF_USE = 0
_BIT_BACKUP_MODE = 4
_BIT_GRID_CHARGING = 5
_BIT_FEED_IN_PRIORITY = 6


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: SolisCloudControlConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        StorageModeSelect(coordinator=coordinator, entity_description=entity_description)
        for entity_description in _ENTITY_DESCRIPTIONS
    )


class StorageModeSelect(SolisCloudControlEntity, SelectEntity):
    def __init__(self, coordinator: SolisCloudControlCoordinator, entity_description: SelectEntityDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_options = [_MODE_SELF_USE, _MODE_FEED_IN_PRIORITY]

    @property
    def current_option(self) -> str | None:
        if not self.coordinator.data:
            return None

        storage_mode_value = self.coordinator.data.get(CID_STORAGE_MODE)
        if storage_mode_value is None:
            return None

        value_int = int(storage_mode_value)

        if value_int & (1 << _BIT_SELF_USE):
            return _MODE_SELF_USE
        elif value_int & (1 << _BIT_FEED_IN_PRIORITY):
            return _MODE_FEED_IN_PRIORITY

        return None

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        attributes = {}

        if self.coordinator.data:
            storage_mode_value = self.coordinator.data.get(CID_STORAGE_MODE)
            if storage_mode_value is not None:
                value_int = int(storage_mode_value)

                battery_reserve = "ON" if value_int & (1 << _BIT_BACKUP_MODE) else "OFF"
                allow_grid_charging = "ON" if value_int & (1 << _BIT_GRID_CHARGING) else "OFF"

                attributes["battery_reserve"] = battery_reserve
                attributes["allow_grid_charging"] = allow_grid_charging

        return attributes

    async def async_select_option(self, option: str) -> None:
        if not self.coordinator.data:
            return

        current_value = self.coordinator.data.get(CID_STORAGE_MODE)
        if current_value is None:
            return

        value_int = int(current_value)

        value_int &= ~(1 << _BIT_SELF_USE)
        value_int &= ~(1 << _BIT_FEED_IN_PRIORITY)

        if option == _MODE_SELF_USE:
            value_int |= 1 << _BIT_SELF_USE
        elif option == _MODE_FEED_IN_PRIORITY:
            value_int |= 1 << _BIT_FEED_IN_PRIORITY

        await self.coordinator.api_client.control(CID_STORAGE_MODE, str(value_int))
        await self.coordinator.async_request_refresh()
