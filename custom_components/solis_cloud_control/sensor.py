from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CID_BATTERY_CAPACITY
from .coordinator import SolisCloudControlCoordinator
from .entity import SolisCloudControlEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:  # noqa: ARG001
    coordinator: SolisCloudControlCoordinator = entry.runtime_data
    async_add_entities(
        [
            BatteryCapacitySensor(
                coordinator=coordinator,
                entity_description=SensorEntityDescription(
                    key="battery_capacity",
                    name="Battery Capacity",
                    icon="mdi:battery",
                ),
                cid=CID_BATTERY_CAPACITY,
            ),
        ]
    )


class BatteryCapacitySensor(SolisCloudControlEntity, SensorEntity):
    def __init__(
        self, coordinator: SolisCloudControlCoordinator, entity_description: SensorEntityDescription, cid: int
    ) -> None:
        super().__init__(coordinator, entity_description, cid)
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None

        value_str = self.coordinator.data.get(self.cid)
        return float(value_str) if value_str is not None else None
