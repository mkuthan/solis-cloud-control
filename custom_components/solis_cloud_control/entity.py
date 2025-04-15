from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.solis_cloud_control.const import CONF_INVERTER_SN
from custom_components.solis_cloud_control.coordinator import SolisCloudControlCoordinator


class SolisCloudControlEntity(CoordinatorEntity[SolisCloudControlCoordinator]):
    def __init__(
        self, coordinator: SolisCloudControlCoordinator, entity_description: EntityDescription, cid: int
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = entity_description
        self.cid = cid

        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{entity_description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    coordinator.config_entry.data[CONF_INVERTER_SN],
                ),
            },
        )

    @property
    def available(self) -> bool:
        return self.coordinator.data.get(self.cid) is not None
