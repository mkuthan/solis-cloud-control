from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CID_BATTERY_FORCE_CHARGE_SOC,
    CID_BATTERY_OVER_DISCHARGE_SOC,
    CID_BATTERY_RESERVE_SOC,
    CID_CHARGE_SLOT1_CURRENT,
    CID_CHARGE_SLOT1_SOC,
    CID_DISCHARGE_SLOT1_CURRENT,
    CID_DISCHARGE_SLOT1_SOC,
)
from .coordinator import SolisCloudControlCoordinator
from .entity import SolisCloudControlEntity


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SolisCloudControlCoordinator = entry.runtime_data
    async_add_entities(
        [
            BatteryCurrent(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="slot1_charge_current",
                    name="Slot1 Charge Current",
                    icon="mdi:battery-plus-outline",
                ),
                cid=CID_CHARGE_SLOT1_CURRENT,
            ),
            BatteryCurrent(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="slot1_discharge_current",
                    name="Slot1 Discharge Current",
                    icon="mdi:battery-minus-outline",
                ),
                cid=CID_DISCHARGE_SLOT1_CURRENT,
            ),
            BatterySoc(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="slot1_charge_soc",
                    name="Slot1 Charge SOC",
                    icon="mdi:battery-plus-outline",
                ),
                cid=CID_CHARGE_SLOT1_SOC,
            ),
            BatterySoc(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="slot1_discharge_soc",
                    name="Slot1 Discharge SOC",
                    icon="mdi:battery-minus-outline",
                ),
                cid=CID_DISCHARGE_SLOT1_SOC,
            ),
            BatterySoc(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="battery_reserve_soc",
                    name="Battery Reserve SOC",
                    icon="mdi:battery-30",
                ),
                cid=CID_BATTERY_RESERVE_SOC,
            ),
            BatterySoc(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="battery_over_discharge_soc",
                    name="Battery Over Discharge SOC",
                    icon="mdi:battery-10",
                ),
                cid=CID_BATTERY_OVER_DISCHARGE_SOC,
            ),
            BatterySoc(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="battery_force_charge_soc",
                    name="Battery Force Charge SOC",
                    icon="mdi:battery-alert-variant-outline",
                ),
                cid=CID_BATTERY_FORCE_CHARGE_SOC,
            ),
        ]
    )


class BatteryCurrent(SolisCloudControlEntity, NumberEntity):
    def __init__(
        self, coordinator: SolisCloudControlCoordinator, entity_description: NumberEntityDescription, cid: int
    ) -> None:
        super().__init__(coordinator, entity_description, cid)
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_device_class = NumberDeviceClass.CURRENT
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None

        value_str = self.coordinator.data.get(self.cid)
        return float(value_str) if value_str is not None else None

    async def async_set_native_value(self, value: float) -> None:
        value_str = str(value)
        await self.coordinator.api_client.control(self.coordinator.inverter_sn, self.cid, value_str)
        await self.coordinator.async_request_refresh()


class BatterySoc(SolisCloudControlEntity, NumberEntity):
    def __init__(
        self, coordinator: SolisCloudControlCoordinator, cid: int, entity_description: NumberEntityDescription
    ) -> None:
        super().__init__(coordinator, entity_description, cid)
        self._attr_native_min_value = 0  # TODO: battery over discharge + 1
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_device_class = NumberDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None

        value_str = self.coordinator.data.get(self.cid)
        return float(value_str) if value_str is not None else None

    async def async_set_native_value(self, value: float) -> None:
        value_str = str(value)
        await self.coordinator.api_client.control(self.coordinator.inverter_sn, self.cid, value_str)
        await self.coordinator.async_request_refresh()
