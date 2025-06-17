import logging

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry
from custom_components.solis_cloud_control.inverters.inverter import InverterStorageMode
from custom_components.solis_cloud_control.utils.safe_converters import safe_get_int_value

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
                inverter_storage_mode=inverter.storage_mode,
            )
        )

    async_add_entities(entities)


class StorageModeSelect(SolisCloudControlEntity, SelectEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: SelectEntityDescription,
        inverter_storage_mode: InverterStorageMode,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_storage_mode.cid)
        self._attr_options = [
            inverter_storage_mode.mode_self_use,
            inverter_storage_mode.mode_feed_in_priority,
            inverter_storage_mode.mode_off_grid,
        ]

        self.inverter_storage_mode = inverter_storage_mode

    @property
    def current_option(self) -> str | None:
        value_str = self.coordinator.data.get(self.inverter_storage_mode.cid)
        value = safe_get_int_value(value_str)
        if value is None:
            return None

        if value & (1 << self.inverter_storage_mode.bit_self_use):
            return self.inverter_storage_mode.mode_self_use
        elif value & (1 << self.inverter_storage_mode.bit_feed_in_priority):
            return self.inverter_storage_mode.mode_feed_in_priority
        elif value & (1 << self.inverter_storage_mode.bit_off_grid):
            return self.inverter_storage_mode.mode_off_grid

        return None

    async def async_select_option(self, option: str) -> None:
        value_str = self.coordinator.data.get(self.inverter_storage_mode.cid)
        value = safe_get_int_value(value_str)
        if value is None:
            return

        # clear the bits for the storage mode options
        new_value = value & ~(
            (1 << self.inverter_storage_mode.bit_self_use)
            | (1 << self.inverter_storage_mode.bit_feed_in_priority)
            | (1 << self.inverter_storage_mode.bit_off_grid)
        )

        if option == self.inverter_storage_mode.mode_self_use:
            new_value |= 1 << self.inverter_storage_mode.bit_self_use
        elif option == self.inverter_storage_mode.mode_feed_in_priority:
            new_value |= 1 << self.inverter_storage_mode.bit_feed_in_priority
        elif option == self.inverter_storage_mode.mode_off_grid:
            new_value |= 1 << self.inverter_storage_mode.bit_off_grid

        _LOGGER.info("Set '%s' to %s (value: %s)", self.name, option, new_value)

        await self.coordinator.control(self.inverter_storage_mode.cid, str(new_value))
