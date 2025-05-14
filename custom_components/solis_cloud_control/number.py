import logging

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberEntityDescription
from homeassistant.const import PERCENTAGE, UnitOfElectricCurrent, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry
from custom_components.solis_cloud_control.inverters.inverter import (
    InverterBatteryMaxChargeCurrent,
    InverterBatteryMaxChargeSOC,
    InverterBatteryMaxDischargeCurrent,
    InverterBatteryOverDischargeSOC,
    InverterChargeDischargeSlot,
    InverterMaxExportPower,
)
from custom_components.solis_cloud_control.utils.safe_converters import safe_get_float_value

from .coordinator import SolisCloudControlCoordinator
from .entity import SolisCloudControlEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: SolisCloudControlConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    inverter = entry.runtime_data.inverter
    coordinator = entry.runtime_data.coordinator

    entities = []

    slots = inverter.charge_discharge_slots

    for i in range(1, slots.SLOTS_COUNT + 1):
        entities.extend(
            [
                BatteryCurrent(
                    coordinator=coordinator,
                    entity_description=NumberEntityDescription(
                        key=f"slot{i}_charge_current",
                        name=f"Slot{i} Charge Current",
                        icon="mdi:battery-plus-outline",
                    ),
                    charge_discharge_slot=slots.get_charge_slot(i),
                    battery_max_charge_discharge_current=inverter.battery_max_charge_current,
                ),
                BatteryCurrent(
                    coordinator=coordinator,
                    entity_description=NumberEntityDescription(
                        key=f"slot{i}_discharge_current",
                        name=f"Slot{i} Discharge Current",
                        icon="mdi:battery-minus-outline",
                    ),
                    charge_discharge_slot=slots.get_discharge_slot(i),
                    battery_max_charge_discharge_current=inverter.battery_max_discharge_current,
                ),
                BatterySoc(
                    coordinator=coordinator,
                    entity_description=NumberEntityDescription(
                        key=f"slot{i}_charge_soc",
                        name=f"Slot{i} Charge SOC",
                        icon="mdi:battery-plus-outline",
                    ),
                    charge_discharge_slot=slots.get_charge_slot(i),
                    battery_over_discharge_soc=inverter.battery_over_discharge_soc,
                    battery_max_charge_soc=inverter.battery_max_charge_soc,
                ),
                BatterySoc(
                    coordinator=coordinator,
                    entity_description=NumberEntityDescription(
                        key=f"slot{i}_discharge_soc",
                        name=f"Slot{i} Discharge SOC",
                        icon="mdi:battery-minus-outline",
                    ),
                    charge_discharge_slot=slots.get_discharge_slot(i),
                    battery_over_discharge_soc=inverter.battery_over_discharge_soc,
                    battery_max_charge_soc=inverter.battery_max_charge_soc,
                ),
            ]
        )

    entities.append(
        MaxExportPower(
            coordinator=coordinator,
            entity_description=NumberEntityDescription(
                key="max_export_power",
                name="Max Export Power",
                icon="mdi:transmission-tower-export",
            ),
            max_export_power=inverter.max_export_power,
        )
    )

    async_add_entities(entities)


class BatteryCurrent(SolisCloudControlEntity, NumberEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: NumberEntityDescription,
        charge_discharge_slot: InverterChargeDischargeSlot,
        battery_max_charge_discharge_current: InverterBatteryMaxChargeCurrent
        | InverterBatteryMaxDischargeCurrent
        | None,
    ) -> None:
        super().__init__(coordinator, entity_description, charge_discharge_slot.current_cid)
        self._attr_native_min_value = charge_discharge_slot.current_min_value
        self._attr_native_step = charge_discharge_slot.current_step
        self._attr_device_class = NumberDeviceClass.CURRENT
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE

        self.charge_discharge_slot = charge_discharge_slot
        self.battery_max_charge_discharge_current = battery_max_charge_discharge_current

    @property
    def native_max_value(self) -> float:
        if self.battery_max_charge_discharge_current is not None:
            battery_max_charge_discharge_current_str = self.coordinator.data.get(
                self.battery_max_charge_discharge_current.cid
            )
            battery_max_charge_discharge_current = safe_get_float_value(battery_max_charge_discharge_current_str)

        if battery_max_charge_discharge_current is not None:
            return battery_max_charge_discharge_current
        else:
            return self.charge_discharge_slot.current_max_value

    @property
    def native_value(self) -> float | None:
        value_str = self.coordinator.data.get(self.charge_discharge_slot.current_cid)
        return safe_get_float_value(value_str)

    async def async_set_native_value(self, value: float) -> None:
        value_str = str(int(round(value)))
        _LOGGER.info("Setting current to %f (value: %s)", value, value_str)
        await self.coordinator.control(self.charge_discharge_slot.current_cid, value_str)


class BatterySoc(SolisCloudControlEntity, NumberEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: NumberEntityDescription,
        charge_discharge_slot: InverterChargeDischargeSlot,
        battery_over_discharge_soc: InverterBatteryOverDischargeSOC | None,
        battery_max_charge_soc: InverterBatteryMaxChargeSOC | None,
    ) -> None:
        super().__init__(coordinator, entity_description, charge_discharge_slot.soc_cid)
        self._attr_native_step = charge_discharge_slot.soc_step
        self._attr_device_class = NumberDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = PERCENTAGE

        self.charge_discharge_slot = charge_discharge_slot
        self.battery_over_discharge_soc = battery_over_discharge_soc
        self.battery_max_charge_soc = battery_max_charge_soc

    @property
    def native_min_value(self) -> float:
        battery_over_discharge = None

        if self.battery_over_discharge_soc is not None:
            battery_over_discharge_str = self.coordinator.data.get(self.battery_over_discharge_soc.cid)
            battery_over_discharge = safe_get_float_value(battery_over_discharge_str)

        if battery_over_discharge is not None:
            return battery_over_discharge + 1
        else:
            return self.charge_discharge_slot.soc_min_value

    @property
    def native_max_value(self) -> float:
        battery_max_charge = None
        if self.battery_max_charge_soc is not None:
            battery_max_charge_str = self.coordinator.data.get(self.battery_max_charge_soc.cid)
            battery_max_charge = safe_get_float_value(battery_max_charge_str)

        if battery_max_charge is not None:
            return battery_max_charge
        else:
            return self.charge_discharge_slot.soc_max_value

    @property
    def native_value(self) -> float | None:
        value_str = self.coordinator.data.get(self.charge_discharge_slot.soc_cid)
        return safe_get_float_value(value_str)

    async def async_set_native_value(self, value: float) -> None:
        value_str = str(int(round(value)))
        _LOGGER.info("Setting SOC to %f (value: %s)", value, value_str)
        await self.coordinator.control(self.charge_discharge_slot.soc_cid, value_str)


class MaxExportPower(SolisCloudControlEntity, NumberEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: NumberEntityDescription,
        max_export_power: InverterMaxExportPower,
    ) -> None:
        super().__init__(coordinator, entity_description, max_export_power.cid)
        self.max_export_power = max_export_power

        self._attr_native_min_value = max_export_power.min_value
        self._attr_native_max_value = max_export_power.max_value
        self._attr_native_step = max_export_power.step
        self._attr_device_class = NumberDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.WATT

    @property
    def native_value(self) -> float | None:
        value_str = self.coordinator.data.get(self.max_export_power.cid)
        value = safe_get_float_value(value_str)
        return value / self.max_export_power.scale if value is not None else None

    async def async_set_native_value(self, value: float) -> None:
        value_str = str(int(round(value * self.max_export_power.scale)))
        _LOGGER.info("Setting max export power to %f (value: %s)", value, value_str)
        await self.coordinator.control(self.max_export_power.cid, value_str)
