from typing import TYPE_CHECKING

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.solis_cloud_control.const import CONF_INVERTER_SN
from custom_components.solis_cloud_control.coordinator import SolisCloudControlCoordinator

if TYPE_CHECKING:
    from homeassistant.helpers.entity import EntityDescription


class SolisCloudControlEntity(CoordinatorEntity[SolisCloudControlCoordinator]):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: EntityDescription,
        cids: int | list[int],
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = entity_description

        assert coordinator.config_entry is not None

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
        return self.coordinator.last_update_success and self._has_data()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # entities are built before the platform adds them, refresh so the first state write is current
        self._refresh_attrs()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._refresh_attrs()
        super()._handle_coordinator_update()

    def _has_data(self) -> bool:
        return all(self.coordinator.data.get(cid) is not None for cid in self.cids)

    def _refresh_attrs(self) -> None:
        # HA does not read state of unavailable entities, parsing missing data would only log noise
        if self._has_data():
            self._update_attrs()

    def _update_attrs(self) -> None:
        """Derive `_attr_*` state from coordinator data, called only when data for all cids is present."""
