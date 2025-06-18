import logging

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry
from custom_components.solis_cloud_control.domain.storage_mode import StorageMode
from custom_components.solis_cloud_control.inverters.inverter import InverterStorageMode

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
    MODE_SELF_USE: str = "Self-Use"
    MODE_FEED_IN_PRIORITY: str = "Feed-In Priority"
    MODE_OFF_GRID: str = "Off-Grid"

    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: SelectEntityDescription,
        inverter_storage_mode: InverterStorageMode,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_storage_mode.cid)
        self._attr_options = [
            self.MODE_SELF_USE,
            self.MODE_FEED_IN_PRIORITY,
            self.MODE_OFF_GRID,
        ]

        self.inverter_storage_mode = inverter_storage_mode

    @property
    def current_option(self) -> str | None:
        current_value = self.coordinator.data.get(self.inverter_storage_mode.cid)

        storage_mode = StorageMode.create(current_value)
        if storage_mode is None:
            _LOGGER.warning("Invalid '%s' storage mode: '%s'", self.name, current_value)
            return None

        if storage_mode.is_self_use():
            return self.MODE_SELF_USE
        elif storage_mode.is_feed_in_priority():
            return self.MODE_FEED_IN_PRIORITY
        elif storage_mode.is_off_grid():
            return self.MODE_OFF_GRID

        return None

    async def async_select_option(self, option: str) -> None:
        current_value = self.coordinator.data.get(self.inverter_storage_mode.cid)

        storage_mode = StorageMode.create(current_value)
        if storage_mode is None:
            _LOGGER.warning("Invalid '%s' storage mode: '%s'", self.name, current_value)
            return None

        if option == self.MODE_SELF_USE:
            storage_mode.set_self_use()
        elif option == self.MODE_FEED_IN_PRIORITY:
            storage_mode.set_feed_in_priority()
        elif option == self.MODE_OFF_GRID:
            storage_mode.set_off_grid()

        value_str = storage_mode.to_value()

        _LOGGER.info("Set '%s' to %s (value: %s)", self.name, option, value_str)
        await self.coordinator.control(self.inverter_storage_mode.cid, value_str)
