from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.solis_cloud_control.coordinator import SolisCloudControlCoordinator


class SolisCloudControlEntity(CoordinatorEntity[SolisCloudControlCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: SolisCloudControlCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    coordinator.config_entry.entry_id,
                ),
            },
        )
