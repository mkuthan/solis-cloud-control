from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.solis_cloud_control.const import CONF_INVERTER_SN
from custom_components.solis_cloud_control.coordinator import SolisCloudControlCoordinator


class SolisCloudControlEntity(CoordinatorEntity[SolisCloudControlCoordinator]):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: EntityDescription,
        cids: int | list[int],
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = entity_description

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

        if isinstance(cids, int):
            self.cids = [cids]
        else:
            self.cids = cids

    @property
    def available(self) -> bool:
        if not self.coordinator.last_update_success:
            return False

        for cid in self.cids:
            if cid not in self.coordinator.data or self.coordinator.data[cid] is None:
                return False

        return True
