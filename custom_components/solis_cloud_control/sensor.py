from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry

from .const import (
    CID_BATTERY_FORCE_CHARGE_SOC,
    CID_BATTERY_MAX_CHARGE_SOC,
    CID_BATTERY_OVER_DISCHARGE_SOC,
    CID_BATTERY_RECOVERY_SOC,
    CID_BATTERY_RESERVE_SOC,
)
from .coordinator import SolisCloudControlCoordinator
from .entity import SolisCloudControlEntity


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: SolisCloudControlConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        [
            BatterySocSensor(
                coordinator=coordinator,
                entity_description=SensorEntityDescription(
                    key="battery_force_charge_soc",
                    name="Battery Force Charge SOC",
                    icon="mdi:battery-alert-variant-outline",
                ),
                cid=CID_BATTERY_FORCE_CHARGE_SOC,
            ),
            BatterySocSensor(
                coordinator=coordinator,
                entity_description=SensorEntityDescription(
                    key="battery_over_discharge_soc",
                    name="Battery Over Discharge SOC",
                    icon="mdi:battery-50",
                ),
                cid=CID_BATTERY_OVER_DISCHARGE_SOC,
            ),
            BatterySocSensor(
                coordinator=coordinator,
                entity_description=SensorEntityDescription(
                    key="battery_recovery_soc",
                    name="Battery Recovery SOC",
                    icon="mdi:battery-50",
                ),
                cid=CID_BATTERY_RECOVERY_SOC,
            ),
            BatterySocSensor(
                coordinator=coordinator,
                entity_description=SensorEntityDescription(
                    key="battery_reserve_soc",
                    name="Battery Reserve SOC",
                    icon="mdi:battery-50",
                ),
                cid=CID_BATTERY_RESERVE_SOC,
            ),
            BatterySocSensor(
                coordinator=coordinator,
                entity_description=SensorEntityDescription(
                    key="battery_max_charge_soc",
                    name="Battery Max Charge SOC",
                    icon="mdi:battery",
                ),
                cid=CID_BATTERY_MAX_CHARGE_SOC,
            ),
        ]
    )


class BatterySocSensor(SolisCloudControlEntity, SensorEntity):
    def __init__(
        self, coordinator: SolisCloudControlCoordinator, entity_description: SensorEntityDescription, cid: int
    ) -> None:
        super().__init__(coordinator, entity_description, cid)
        self._attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> float | None:
        value_str = self.coordinator.data.get(self.cid)
        return float(value_str) if value_str is not None else None
