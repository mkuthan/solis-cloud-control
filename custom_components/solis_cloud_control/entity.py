from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from .api import SolisCloudControlApiClient
from .const import (
    DOMAIN,
    LOGGER,
    STORAGE_MODE_BIT_BACKUP_MODE,
    STORAGE_MODE_BIT_FEED_IN_PRIORITY,
    STORAGE_MODE_BIT_GRID_CHARGING,
    STORAGE_MODE_BIT_SELF_USE,
    STORAGE_MODE_CID,
)


class StorageModeEntity(SelectEntity):
    def __init__(self, hass: HomeAssistant, client: SolisCloudControlApiClient, serial_number: str) -> None:
        self._hass = hass
        self._client = client
        self._attr_name = "Storage Mode"
        self._attr_unique_id = f"{serial_number}_storage_mode"
        self.entity_id = f"select.solis_storage_mode_{serial_number.lower()}"
        self._attr_options = ["Self Use", "Feed In Priority"]
        self._attr_current_option = "Self Use"
        self._battery_reserve = "ON"
        self._allow_grid_charging = "OFF"
        self._attr_available = True
        self._attr_icon = "mdi:battery-charging"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial_number)},
            name=f"Solis Inverter {serial_number}",
            manufacturer="Solis",
            model="Inverter",
        )

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return {
            "battery_reserve": self._battery_reserve,
            "allow_grid_charging": self._allow_grid_charging,
        }

    async def async_update(self) -> None:
        try:
            result = await self._client.read(STORAGE_MODE_CID)
            value_int = int(result)

            if value_int & (1 << STORAGE_MODE_BIT_SELF_USE):
                self._attr_current_option = "Self Use"
            elif value_int & (1 << STORAGE_MODE_BIT_FEED_IN_PRIORITY):
                self._attr_current_option = "Feed In Priority"

            self._battery_reserve = "ON" if value_int & (1 << STORAGE_MODE_BIT_BACKUP_MODE) else "OFF"
            self._allow_grid_charging = "ON" if value_int & (1 << STORAGE_MODE_BIT_GRID_CHARGING) else "OFF"

            self._attr_available = True
            self.async_write_ha_state()
        except Exception as err:
            LOGGER.error("Failed to update storage mode: %s", err)
            self._attr_available = False
            self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        value_int = 0

        if option == "Self Use":
            value_int |= 1 << STORAGE_MODE_BIT_SELF_USE
        elif option == "Feed In Priority":
            value_int |= 1 << STORAGE_MODE_BIT_FEED_IN_PRIORITY

        if self._battery_reserve == "ON":
            value_int |= 1 << STORAGE_MODE_BIT_BACKUP_MODE

        if self._allow_grid_charging == "ON":
            value_int |= 1 << STORAGE_MODE_BIT_GRID_CHARGING

        value = str(value_int)

        await self._client.control(STORAGE_MODE_CID, value)
        self._attr_current_option = option
        self.async_write_ha_state()

    async def async_set_battery_reserve(self, state: str) -> None:
        self._battery_reserve = state
        await self.async_select_option(self._attr_current_option)

    async def async_set_allow_grid_charging(self, state: str) -> None:
        self._allow_grid_charging = state
        await self.async_select_option(self._attr_current_option)
