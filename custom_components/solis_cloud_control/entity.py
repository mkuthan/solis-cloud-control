from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.solis_cloud_control.const import CONF_INVERTER_SN
from custom_components.solis_cloud_control.coordinator import SolisCloudControlCoordinator


class SolisCloudControlEntity(CoordinatorEntity[SolisCloudControlCoordinator]):
    def __init__(self, coordinator: SolisCloudControlCoordinator, cid: int) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{cid}"
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    coordinator.config_entry.data[CONF_INVERTER_SN],
                ),
            },
        )
        self.cid = cid
