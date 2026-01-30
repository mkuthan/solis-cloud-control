import logging
from typing import Literal

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.const import PERCENTAGE, UnitOfElectricCurrent, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry
from custom_components.solis_cloud_control.domain.charge_discharge_settings import ChargeDischargeSettings
from custom_components.solis_cloud_control.inverters.inverter import (
    InverterBatteryForceChargeSOC,
    InverterBatteryMaxChargeCurrent,
    InverterBatteryMaxChargeSOC,
    InverterBatteryMaxDischargeCurrent,
    InverterBatteryOverDischargeSOC,
    InverterBatteryRecoverySOC,
    InverterBatteryReserveSOC,
    InverterChargeDischargeSettings,
    InverterChargeDischargeSlot,
    InverterMaxExportPower,
    InverterMaxOutputPower,
    InverterPowerLimit,
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

    charge_discharge_settings = inverter.charge_discharge_settings

    if charge_discharge_settings is not None:
        for i in range(1, charge_discharge_settings.SLOTS_COUNT + 1):
            entities.extend(
                [
                    BatteryCurrentV1(
                        coordinator=coordinator,
                        entity_description=NumberEntityDescription(
                            key=f"slot{i}_charge_current_v1",
                            name=f"Slot{i} Charge Current",
                            icon="mdi:battery-plus-outline",
                        ),
                        inverter_charge_discharge_settings=charge_discharge_settings,
                        inverter_battery_max_charge_discharge_current=inverter.battery_max_charge_current,
                        slot_number=i,
                        slot_type="charge",
                    ),
                    BatteryCurrentV1(
                        coordinator=coordinator,
                        entity_description=NumberEntityDescription(
                            key=f"slot{i}_discharge_current_v1",
                            name=f"Slot{i} Discharge Current",
                            icon="mdi:battery-minus-outline",
                        ),
                        inverter_charge_discharge_settings=charge_discharge_settings,
                        inverter_battery_max_charge_discharge_current=inverter.battery_max_charge_current,
                        slot_number=i,
                        slot_type="discharge",
                    ),
                ]
            )

    charge_discharge_slots = inverter.charge_discharge_slots

    if charge_discharge_slots is not None:
        for i in range(1, charge_discharge_slots.SLOTS_COUNT + 1):
            entities.extend(
                [
                    BatteryCurrentV2(
                        coordinator=coordinator,
                        entity_description=NumberEntityDescription(
                            key=f"slot{i}_charge_current",  # don't use _v2 suffix for backwards compatibility
                            name=f"Slot{i} Charge Current",
                            icon="mdi:battery-plus-outline",
                        ),
                        inverter_charge_discharge_slot=charge_discharge_slots.get_charge_slot(i),
                        inverter_battery_max_charge_discharge_current=inverter.battery_max_charge_current,
                    ),
                    BatteryCurrentV2(
                        coordinator=coordinator,
                        entity_description=NumberEntityDescription(
                            key=f"slot{i}_discharge_current",  # don't use _v2 suffix for backwards compatibility
                            name=f"Slot{i} Discharge Current",
                            icon="mdi:battery-minus-outline",
                        ),
                        inverter_charge_discharge_slot=charge_discharge_slots.get_discharge_slot(i),
                        inverter_battery_max_charge_discharge_current=inverter.battery_max_discharge_current,
                    ),
                    BatterySocV2(
                        coordinator=coordinator,
                        entity_description=NumberEntityDescription(
                            key=f"slot{i}_charge_soc",  # don't use _v2 suffix for backwards compatibility
                            name=f"Slot{i} Charge SOC",
                            icon="mdi:battery-plus-outline",
                        ),
                        inverter_charge_discharge_slot=charge_discharge_slots.get_charge_slot(i),
                        inverter_battery_over_discharge_soc=inverter.battery_over_discharge_soc,
                        inverter_battery_max_charge_soc=inverter.battery_max_charge_soc,
                    ),
                    BatterySocV2(
                        coordinator=coordinator,
                        entity_description=NumberEntityDescription(
                            key=f"slot{i}_discharge_soc",  # don't use _v2 suffix for backwards compatibility
                            name=f"Slot{i} Discharge SOC",
                            icon="mdi:battery-minus-outline",
                        ),
                        inverter_charge_discharge_slot=charge_discharge_slots.get_discharge_slot(i),
                        inverter_battery_over_discharge_soc=inverter.battery_over_discharge_soc,
                        inverter_battery_max_charge_soc=inverter.battery_max_charge_soc,
                    ),
                ]
            )

    if inverter.battery_force_charge_soc:
        entities.append(
            BatterySocNumber(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="battery_force_charge_soc",
                    name="Battery Force Charge SOC",
                    icon="mdi:battery-alert",
                ),
                inverter_battery_soc=inverter.battery_force_charge_soc,
            )
        )
    if inverter.battery_over_discharge_soc:
        entities.append(
            BatterySocNumber(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="battery_over_discharge_soc",
                    name="Battery Over Discharge SOC",
                    icon="mdi:battery-50",
                ),
                inverter_battery_soc=inverter.battery_over_discharge_soc,
            )
        )
    if inverter.battery_recovery_soc:
        entities.append(
            BatterySocNumber(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="battery_recovery_soc",
                    name="Battery Recovery SOC",
                    icon="mdi:battery-50",
                ),
                inverter_battery_soc=inverter.battery_recovery_soc,
            )
        )
    if inverter.battery_reserve_soc:
        entities.append(
            BatterySocNumber(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="battery_reserve_soc",
                    name="Battery Reserve SOC",
                    icon="mdi:battery-50",
                ),
                inverter_battery_soc=inverter.battery_reserve_soc,
            )
        )
    if inverter.battery_max_charge_soc:
        entities.append(
            BatterySocNumber(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="battery_max_charge_soc",
                    name="Battery Max Charge SOC",
                    icon="mdi:battery",
                ),
                inverter_battery_soc=inverter.battery_max_charge_soc,
            )
        )
    if inverter.battery_max_charge_current:
        entities.append(
            BatteryMaxCurrentNumber(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="battery_max_charge_current",
                    name="Battery Max Charge Current",
                    icon="mdi:battery-arrow-down-outline",
                ),
                inverter_battery_max_current=inverter.battery_max_charge_current,
            )
        )
    if inverter.battery_max_discharge_current:
        entities.append(
            BatteryMaxCurrentNumber(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="battery_max_discharge_current",
                    name="Battery Max Discharge Current",
                    icon="mdi:battery-arrow-up-outline",
                ),
                inverter_battery_max_current=inverter.battery_max_discharge_current,
            )
        )

    if inverter.max_output_power is not None:
        entities.append(
            MaxOutputPower(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="max_output_power",
                    name="Max Output Power",
                    icon="mdi:lightning-bolt-outline",
                ),
                inverter_max_output_power=inverter.max_output_power,
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
                inverter_max_export_power=inverter.max_export_power,
            )
        )

    if inverter.power_limit is not None:
        entities.append(
            PowerLimit(
                coordinator=coordinator,
                entity_description=NumberEntityDescription(
                    key="power_limit",
                    name="Power Limit",
                    icon="mdi:transmission-tower-export",
                ),
                inverter_power_limit=inverter.power_limit,
            )
        )

    async_add_entities(entities)


class BatteryCurrentV1(SolisCloudControlEntity, NumberEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: NumberEntityDescription,
        inverter_charge_discharge_settings: InverterChargeDischargeSettings,
        inverter_battery_max_charge_discharge_current: InverterBatteryMaxChargeCurrent
        | InverterBatteryMaxDischargeCurrent
        | None,
        slot_number: int,
        slot_type: Literal["charge", "discharge"],
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_charge_discharge_settings.cid)
        self._attr_native_min_value = inverter_charge_discharge_settings.current_min_value
        self._attr_native_step = inverter_charge_discharge_settings.current_step
        self._attr_device_class = NumberDeviceClass.CURRENT
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
        self._attr_mode = NumberMode.BOX

        self.inverter_charge_discharge_settings = inverter_charge_discharge_settings
        self.inverter_battery_max_charge_discharge_current = inverter_battery_max_charge_discharge_current
        self.slot_number = slot_number
        self.slot_type = slot_type

    @property
    def native_max_value(self) -> float:
        if self.inverter_battery_max_charge_discharge_current is not None:
            battery_max_charge_discharge_current_str = self.coordinator.data.get(
                self.inverter_battery_max_charge_discharge_current.cid
            )
            battery_max_charge_discharge_current = safe_get_float_value(battery_max_charge_discharge_current_str)

            if battery_max_charge_discharge_current is not None:
                parallel_battery_count = self.inverter_battery_max_charge_discharge_current.parallel_battery_count
                return battery_max_charge_discharge_current * parallel_battery_count

        return self.inverter_charge_discharge_settings.current_max_value

    @property
    def native_value(self) -> float | None:
        current_value = self.coordinator.data.get(self.inverter_charge_discharge_settings.cid)

        charge_discharge_settings = ChargeDischargeSettings.create(current_value)
        if charge_discharge_settings is None:
            _LOGGER.warning("Invalid '%s' settings: '%s'", self.name, current_value)
            return None

        if self.slot_type == "charge":
            current = charge_discharge_settings.get_charge_current(self.slot_number)
        else:
            current = charge_discharge_settings.get_discharge_current(self.slot_number)

        return current

    async def async_set_native_value(self, value: float) -> None:
        current_value = self.coordinator.data.get(self.inverter_charge_discharge_settings.cid)
        charge_discharge_settings = ChargeDischargeSettings.create(current_value)

        if charge_discharge_settings is None:
            _LOGGER.warning("Invalid '%s' settings: '%s'", self.name, current_value)
            return None

        if self.slot_type == "charge":
            charge_discharge_settings.set_charge_current(self.slot_number, value)
        else:
            charge_discharge_settings.set_discharge_current(self.slot_number, value)

        value_str = charge_discharge_settings.to_value()

        _LOGGER.info("Set '%s' to %f (value: %s)", self.name, value, value_str)
        await self.coordinator.control(self.inverter_charge_discharge_settings.cid, value_str)


class BatteryCurrentV2(SolisCloudControlEntity, NumberEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: NumberEntityDescription,
        inverter_charge_discharge_slot: InverterChargeDischargeSlot,
        inverter_battery_max_charge_discharge_current: InverterBatteryMaxChargeCurrent
        | InverterBatteryMaxDischargeCurrent
        | None,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_charge_discharge_slot.current_cid)
        self._attr_native_min_value = inverter_charge_discharge_slot.current_min_value
        self._attr_native_step = inverter_charge_discharge_slot.current_step
        self._attr_device_class = NumberDeviceClass.CURRENT
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
        self._attr_mode = NumberMode.BOX

        self.inverter_charge_discharge_slot = inverter_charge_discharge_slot
        self.inverter_battery_max_charge_discharge_current = inverter_battery_max_charge_discharge_current

    @property
    def native_max_value(self) -> float:
        if self.inverter_battery_max_charge_discharge_current is not None:
            battery_max_charge_discharge_current_str = self.coordinator.data.get(
                self.inverter_battery_max_charge_discharge_current.cid
            )
            battery_max_charge_discharge_current = safe_get_float_value(battery_max_charge_discharge_current_str)

            if battery_max_charge_discharge_current is not None:
                parallel_battery_count = self.inverter_battery_max_charge_discharge_current.parallel_battery_count
                return battery_max_charge_discharge_current * parallel_battery_count

        return self.inverter_charge_discharge_slot.current_max_value

    @property
    def native_value(self) -> float | None:
        value_str = self.coordinator.data.get(self.inverter_charge_discharge_slot.current_cid)
        return safe_get_float_value(value_str)

    async def async_set_native_value(self, value: float) -> None:
        value_str = str(int(round(value)))
        _LOGGER.info("Set '%s' to %f (value: %s)", self.name, value, value_str)
        await self.coordinator.control(self.inverter_charge_discharge_slot.current_cid, value_str)


class BatterySocV2(SolisCloudControlEntity, NumberEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: NumberEntityDescription,
        inverter_charge_discharge_slot: InverterChargeDischargeSlot,
        inverter_battery_over_discharge_soc: InverterBatteryOverDischargeSOC | None,
        inverter_battery_max_charge_soc: InverterBatteryMaxChargeSOC | None,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_charge_discharge_slot.soc_cid)
        self._attr_native_step = inverter_charge_discharge_slot.soc_step
        self._attr_device_class = NumberDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_mode = NumberMode.BOX

        self.inverter_charge_discharge_slot = inverter_charge_discharge_slot
        self.inverter_battery_over_discharge_soc = inverter_battery_over_discharge_soc
        self.inverter_battery_max_charge_soc = inverter_battery_max_charge_soc

    @property
    def native_min_value(self) -> float:
        battery_over_discharge = None

        if self.inverter_battery_over_discharge_soc is not None:
            battery_over_discharge_str = self.coordinator.data.get(self.inverter_battery_over_discharge_soc.cid)
            battery_over_discharge = safe_get_float_value(battery_over_discharge_str)

        if battery_over_discharge is not None:
            return battery_over_discharge + 1
        else:
            return self.inverter_charge_discharge_slot.soc_min_value

    @property
    def native_max_value(self) -> float:
        battery_max_charge = None
        if self.inverter_battery_max_charge_soc is not None:
            battery_max_charge_str = self.coordinator.data.get(self.inverter_battery_max_charge_soc.cid)
            battery_max_charge = safe_get_float_value(battery_max_charge_str)

        if battery_max_charge is not None:
            return battery_max_charge
        else:
            return self.inverter_charge_discharge_slot.soc_max_value

    @property
    def native_value(self) -> float | None:
        value_str = self.coordinator.data.get(self.inverter_charge_discharge_slot.soc_cid)
        return safe_get_float_value(value_str)

    async def async_set_native_value(self, value: float) -> None:
        value_str = str(int(round(value)))
        _LOGGER.info("Set '%s' to %f (value: %s)", self.name, value, value_str)
        await self.coordinator.control(self.inverter_charge_discharge_slot.soc_cid, value_str)


class MaxOutputPower(SolisCloudControlEntity, NumberEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: NumberEntityDescription,
        inverter_max_output_power: InverterMaxOutputPower,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_max_output_power.cid)
        self.inverter_max_output_power = inverter_max_output_power

        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_mode = NumberMode.BOX

    @property
    def native_value(self) -> float | None:
        value_str = self.coordinator.data.get(self.inverter_max_output_power.cid)
        return safe_get_float_value(value_str)

    async def async_set_native_value(self, value: float) -> None:
        value_str = str(int(round(value)))
        _LOGGER.info("Set '%s' to %f (value: %s)", self.name, value, value_str)
        await self.coordinator.control(self.inverter_max_output_power.cid, value_str)


class MaxExportPower(SolisCloudControlEntity, NumberEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: NumberEntityDescription,
        inverter_max_export_power: InverterMaxExportPower,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_max_export_power.cid)
        self.inverter_max_export_power = inverter_max_export_power

        self._attr_native_min_value = inverter_max_export_power.min_value
        self._attr_native_max_value = inverter_max_export_power.max_value
        self._attr_native_step = inverter_max_export_power.step
        self._attr_device_class = NumberDeviceClass.POWER
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_mode = NumberMode.BOX

    @property
    def native_value(self) -> float | None:
        value_str = self.coordinator.data.get(self.inverter_max_export_power.cid)
        value = safe_get_float_value(value_str)
        return value / self.inverter_max_export_power.scale if value is not None else None

    async def async_set_native_value(self, value: float) -> None:
        value_str = str(int(round(value * self.inverter_max_export_power.scale)))
        _LOGGER.info("Set '%s' to %f (value: %s)", self.name, value, value_str)
        await self.coordinator.control(self.inverter_max_export_power.cid, value_str)


class PowerLimit(SolisCloudControlEntity, NumberEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: NumberEntityDescription,
        inverter_power_limit: InverterPowerLimit,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_power_limit.cid)
        self.inverter_power_limit = inverter_power_limit

        self._attr_native_min_value = inverter_power_limit.min_value
        self._attr_native_max_value = inverter_power_limit.max_value
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_mode = NumberMode.BOX

    @property
    def native_value(self) -> float | None:
        value_str = self.coordinator.data.get(self.inverter_power_limit.cid)
        return safe_get_float_value(value_str)

    async def async_set_native_value(self, value: float) -> None:
        value_str = str(int(round(value)))
        _LOGGER.info("Set '%s' to %f (value: %s)", self.name, value, value_str)
        await self.coordinator.control(self.inverter_power_limit.cid, value_str)


class BatterySocNumber(SolisCloudControlEntity, NumberEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: NumberEntityDescription,
        inverter_battery_soc: InverterBatteryReserveSOC
        | InverterBatteryOverDischargeSOC
        | InverterBatteryForceChargeSOC
        | InverterBatteryRecoverySOC
        | InverterBatteryMaxChargeSOC,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_battery_soc.cid)
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_device_class = NumberDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_mode = NumberMode.BOX

        self.inverter_battery_soc = inverter_battery_soc

    @property
    def native_value(self) -> float | None:
        value_str = self.coordinator.data.get(self.inverter_battery_soc.cid)
        return safe_get_float_value(value_str)

    async def async_set_native_value(self, value: float) -> None:
        value_str = str(int(round(value)))
        _LOGGER.info("Set '%s' to %f (value: %s)", self.name, value, value_str)
        await self.coordinator.control(self.inverter_battery_soc.cid, value_str)


class BatteryMaxCurrentNumber(SolisCloudControlEntity, NumberEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: NumberEntityDescription,
        inverter_battery_max_current: InverterBatteryMaxChargeCurrent | InverterBatteryMaxDischargeCurrent,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_battery_max_current.cid)
        self._attr_native_min_value = inverter_battery_max_current.min_value
        self._attr_native_max_value = inverter_battery_max_current.max_value
        self._attr_native_step = inverter_battery_max_current.step
        self._attr_device_class = NumberDeviceClass.CURRENT
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
        self._attr_mode = NumberMode.BOX

        self.inverter_battery_max_current = inverter_battery_max_current

    @property
    def native_value(self) -> float | None:
        value_str = self.coordinator.data.get(self.inverter_battery_max_current.cid)
        return safe_get_float_value(value_str)

    async def async_set_native_value(self, value: float) -> None:
        value_str = str(int(round(value)))
        _LOGGER.info("Set '%s' to %f (value: %s)", self.name, value, value_str)
        await self.coordinator.control(self.inverter_battery_max_current.cid, value_str)
