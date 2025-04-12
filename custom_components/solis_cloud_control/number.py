import logging

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberEntityDescription
from homeassistant.const import PERCENTAGE, UnitOfElectricCurrent, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry

from .const import (
    CID_BATTERY_OVER_DISCHARGE_SOC,
    CID_CHARGE_SLOT1_CURRENT,
    CID_CHARGE_SLOT1_SOC,
    CID_DISCHARGE_SLOT1_CURRENT,
    CID_DISCHARGE_SLOT1_SOC,
    CID_MAX_EXPORT_POWER,
)
from .coordinator import SolisCloudControlCoordinator
from .entity import SolisCloudControlEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: SolisCloudControlConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
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
            MaxExportPower(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="max_export_power",
                    name="Max Export Power",
                    icon="mdi:transmission-tower-export",
                ),
                cid=CID_MAX_EXPORT_POWER,
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
        _LOGGER.info("Setting current to %f (value: %s)", value, value_str)
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
        _LOGGER.info("Setting SOC to %f (value: %s)", value, value_str)
        await self.coordinator.control(self.cid, value_str)


class MaxExportPower(SolisCloudControlEntity, NumberEntity):
    def __init__(
        self, coordinator: SolisCloudControlCoordinator, entity_description: NumberEntityDescription, cid: int
    ) -> None:
        super().__init__(coordinator, entity_description, cid)
        self._attr_native_min_value = 0
        self._attr_native_max_value = 13200
        self._attr_native_step = 100
        self._attr_device_class = NumberDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.WATT

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        value_str = self.coordinator.data.get(self.cid)
        return float(value_str) * 100 if value_str is not None else None

    async def async_set_native_value(self, value: float) -> None:
        value_str = str(int(round(value / 100)))
        _LOGGER.info("Setting max export power to %f (value: %s)", value, value_str)
        await self.coordinator.control(self.cid, value_str)
