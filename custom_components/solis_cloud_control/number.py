import logging

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CID_BATTERY_OVER_DISCHARGE_SOC,
    CID_CHARGE_SLOT1_CURRENT,
    CID_CHARGE_SLOT1_SOC,
    CID_DISCHARGE_SLOT1_CURRENT,
    CID_DISCHARGE_SLOT1_SOC,
)
from .coordinator import SolisCloudControlCoordinator
from .entity import SolisCloudControlEntity

_LOGGER = logging.getLogger(__name__)


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
        value_str = str(int(round(value)))
        _LOGGER.info("Setting current to %s", value_str)
        await self.coordinator.control(self.cid, value_str)


class BatterySoc(SolisCloudControlEntity, NumberEntity):
    def __init__(
        self, coordinator: SolisCloudControlCoordinator, cid: int, entity_description: NumberEntityDescription
    ) -> None:
        super().__init__(coordinator, entity_description, cid)
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_device_class = NumberDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_min_value(self) -> float:
        if not self.coordinator.data:
            return 0
        over_discharge_str = self.coordinator.data.get(CID_BATTERY_OVER_DISCHARGE_SOC)
        return float(over_discharge_str) + 1 if over_discharge_str is not None else 0

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None

        value_str = self.coordinator.data.get(self.cid)
        return float(value_str) if value_str is not None else None

    async def async_set_native_value(self, value: float) -> None:
        value_str = str(int(round(value)))
        _LOGGER.info("Setting SOC to %s", value_str)
        await self.coordinator.control(self.cid, value_str)
