import logging

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberEntityDescription
from homeassistant.const import PERCENTAGE, UnitOfElectricCurrent, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry
from custom_components.solis_cloud_control.inverter import (
    InverterBatteryMaxChargeSOC,
    InverterBatteryOverDischargeSOC,
    InverterChargeDischargeSlot,
    InverterMaxChargingCurrent,
    InverterMaxDischargingCurrent,
    InverterMaxExportPower,
)
from custom_components.solis_cloud_control.safe_converters import safe_get_float_value

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

    if inverter.charge_discharge_slots is not None:
        entities.append(
            BatteryCurrent(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="slot1_charge_current",
                    name="Slot1 Charge Current",
                    icon="mdi:battery-plus-outline",
                ),
                charge_discharge_slot=inverter.charge_discharge_slots.charge_slot1,
                max_charging_discharging_current=inverter.max_charging_current,
            )
        )
        entities.append(
            BatteryCurrent(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="slot1_discharge_current",
                    name="Slot1 Discharge Current",
                    icon="mdi:battery-minus-outline",
                ),
                charge_discharge_slot=inverter.charge_discharge_slots.discharge_slot1,
                max_charging_discharging_current=inverter.max_discharging_current,
            )
        )
        entities.append(
            BatterySoc(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="slot1_charge_soc",
                    name="Slot1 Charge SOC",
                    icon="mdi:battery-plus-outline",
                ),
                charge_discharge_slot=inverter.charge_discharge_slots.charge_slot1,
                battery_over_discharge_soc=inverter.battery_over_discharge_soc,
                battery_max_charge_soc=inverter.battery_max_charge_soc,
            )
        )
        entities.append(
            BatterySoc(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="slot1_discharge_soc",
                    name="Slot1 Discharge SOC",
                    icon="mdi:battery-minus-outline",
                ),
                charge_discharge_slot=inverter.charge_discharge_slots.discharge_slot1,
                battery_over_discharge_soc=inverter.battery_over_discharge_soc,
                battery_max_charge_soc=inverter.battery_max_charge_soc,
            )
        )

    if inverter.max_export_power is not None:
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
        max_charging_discharging_current: InverterMaxChargingCurrent | InverterMaxDischargingCurrent | None,
    ) -> None:
        super().__init__(coordinator, entity_description)
        self._attr_native_min_value = charge_discharge_slot.current_min_value
        self._attr_native_step = charge_discharge_slot.current_step
        self._attr_device_class = NumberDeviceClass.CURRENT
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE

        self.charge_discharge_slot = charge_discharge_slot
        self.max_charging_discharging_current = max_charging_discharging_current

    @property
    def native_max_value(self) -> float:
        max_charging_discharging_current = None

        if self.max_charging_discharging_current is not None:
            max_charging_discharging_current_str = self.coordinator.data.get(self.max_charging_discharging_current.cid)
            max_charging_discharging_current = safe_get_float_value(max_charging_discharging_current_str)

        if max_charging_discharging_current is not None:
            return max_charging_discharging_current
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
        super().__init__(coordinator, entity_description)
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
        super().__init__(coordinator, entity_description)
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
