import logging

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry
from custom_components.solis_cloud_control.inverter import InverterStorageMode
from custom_components.solis_cloud_control.number_utils import safe_get_int_value

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

    if inverter.storage_mode is not None:
        entities.append(
            StorageModeSelect(
                coordinator=coordinator,
                entity_description=SelectEntityDescription(
                    key="storage_mode",
                    name="Storage Mode",
                    icon="mdi:solar-power",
                ),
                storage_mode=inverter.storage_mode,
            ),
        )

    async_add_entities(entities)


class StorageModeSelect(SolisCloudControlEntity, SelectEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: SelectEntityDescription,
        storage_mode: InverterStorageMode,
    ) -> None:
        super().__init__(coordinator, entity_description)
        self._attr_options = [
            storage_mode.mode_self_use,
            storage_mode.mode_feed_in_priority,
            storage_mode.mode_off_grid,
        ]

        self.storage_mode = storage_mode

    @property
    def current_option(self) -> str | None:
        value_str = self.coordinator.data.get(self.storage_mode.cid)
        value = safe_get_int_value(value_str)
        if value is None:
            return None

        if value & (1 << self.storage_mode.bit_self_use):
            return self.storage_mode.mode_self_use
        elif value & (1 << self.storage_mode.bit_feed_in_priority):
            return self.storage_mode.mode_feed_in_priority
        elif value & (1 << self.storage_mode.bit_off_grid):
            return self.storage_mode.mode_off_grid

        return None

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        value_str = self.coordinator.data.get(self.storage_mode.cid)
        value = safe_get_int_value(value_str)

        attributes = {}
        if value is not None:
            battery_reserve = "ON" if value & (1 << self.storage_mode.bit_backup_mode) else "OFF"
            allow_grid_charging = "ON" if value & (1 << self.storage_mode.bit_grid_charging) else "OFF"

            attributes["battery_reserve"] = battery_reserve
            attributes["allow_grid_charging"] = allow_grid_charging

        return attributes

    async def async_select_option(self, option: str) -> None:
        value_str = self.coordinator.data.get(self.storage_mode.cid)
        value = safe_get_int_value(value_str)
        if value is None:
            return

        value &= ~(1 << self.storage_mode.bit_self_use)
        value &= ~(1 << self.storage_mode.bit_feed_in_priority)
        value &= ~(1 << self.storage_mode.bit_off_grid)

        if option == self.storage_mode.mode_self_use:
            value |= 1 << self.storage_mode.bit_self_use
        elif option == self.storage_mode.mode_feed_in_priority:
            value |= 1 << self.storage_mode.bit_feed_in_priority
        elif option == self.storage_mode.mode_off_grid:
            value |= 1 << self.storage_mode.bit_off_grid

        _LOGGER.info("Setting storage mode to %s (value: %s)", option, value)

        await self.coordinator.control(self.storage_mode.cid, str(value))
