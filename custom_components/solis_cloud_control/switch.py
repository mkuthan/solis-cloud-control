import logging

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry
from custom_components.solis_cloud_control.inverters.inverter import (
    InverterChargeDischargeSlot,
    InverterChargeDischargeSlots,
    InverterOnOff,
    InverterStorageMode,
)
from custom_components.solis_cloud_control.utils.safe_converters import safe_get_int_value

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

    if inverter.on_off is not None:
        entities.append(
            OnOffSwitch(
                coordinator=coordinator,
                entity_description=SwitchEntityDescription(
                    key="on_off_switch",
                    name="Inverter On/Off",
                    icon="mdi:power",
                ),
                inverter_on_off=inverter.on_off,
            )
        )

    charge_discharge_slots = inverter.charge_discharge_slots

    if charge_discharge_slots is not None:
        for i in range(1, charge_discharge_slots.SLOTS_COUNT + 1):
            entities.append(
                SlotV2Switch(
                    coordinator=coordinator,
                    entity_description=SwitchEntityDescription(
                        key=f"slot{i}_charge_switch",
                        name=f"Slot{i} Charge",
                        icon="mdi:battery-plus-outline",
                    ),
                    inverter_charge_discharge_slot=charge_discharge_slots.get_charge_slot(i),
                    inverter_charge_discharge_slots=charge_discharge_slots,
                )
            )
            entities.append(
                SlotV2Switch(
                    coordinator=coordinator,
                    entity_description=SwitchEntityDescription(
                        key=f"slot{i}_discharge_switch",
                        name=f"Slot{i} Discharge",
                        icon="mdi:battery-minus-outline",
                    ),
                    inverter_charge_discharge_slot=charge_discharge_slots.get_discharge_slot(i),
                    inverter_charge_discharge_slots=charge_discharge_slots,
                )
            )

    if inverter.storage_mode is not None:
        entities.append(
            BatteryReserveSwitch(
                coordinator=coordinator,
                entity_description=SwitchEntityDescription(
                    key="battery_reserve",
                    name="Battery Reserve",
                    icon="mdi:battery-heart-outline",
                ),
                inverter_storage_mode=inverter.storage_mode,
            )
        )
        entities.append(
            AllowGridChargingSwitch(
                coordinator=coordinator,
                entity_description=SwitchEntityDescription(
                    key="allow_grid_charging",
                    name="Allow Grid Charging",
                    icon="mdi:battery-charging-outline",
                ),
                inverter_storage_mode=inverter.storage_mode,
            )
        )

    async_add_entities(entities)


class OnOffSwitch(SolisCloudControlEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: SwitchEntityDescription,
        inverter_on_off: InverterOnOff,
    ) -> None:
        super().__init__(coordinator, entity_description, [inverter_on_off.on_cid, inverter_on_off.off_cid])
        self.inverter_on_off = inverter_on_off

    @property
    def assumed_state(self) -> bool:
        on_value = self.coordinator.data.get(self.inverter_on_off.on_cid)
        off_value = self.coordinator.data.get(self.inverter_on_off.off_cid)

        same_values = on_value == off_value
        valid_values = self.inverter_on_off.is_valid_value(on_value) and self.inverter_on_off.is_valid_value(off_value)

        return not (same_values and valid_values)

    @property
    def is_on(self) -> bool | None:
        on_value = self.coordinator.data.get(self.inverter_on_off.on_cid)
        off_value = self.coordinator.data.get(self.inverter_on_off.off_cid)

        same_values = on_value == off_value
        valid_values = self.inverter_on_off.is_valid_value(on_value) and self.inverter_on_off.is_valid_value(off_value)

        if same_values and valid_values:
            return on_value == self.inverter_on_off.on_value

        return None

    async def async_turn_on(self, **kwargs: dict[str, any]) -> None:  # noqa: ARG002
        _LOGGER.info("Turn on '%s'", self.name)
        if self.assumed_state:
            await self.coordinator.control_no_check(self.inverter_on_off.on_cid, self.inverter_on_off.on_value)
        else:
            await self.coordinator.control(self.inverter_on_off.on_cid, self.inverter_on_off.on_value)

    async def async_turn_off(self, **kwargs: dict[str, any]) -> None:  # noqa: ARG002
        _LOGGER.info("Turn off '%s'", self.name)
        if self.assumed_state:
            await self.coordinator.control_no_check(self.inverter_on_off.off_cid, self.inverter_on_off.off_value)
        else:
            await self.coordinator.control(self.inverter_on_off.off_cid, self.inverter_on_off.off_value)


class SlotV2Switch(SolisCloudControlEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: SwitchEntityDescription,
        inverter_charge_discharge_slot: InverterChargeDischargeSlot,
        inverter_charge_discharge_slots: InverterChargeDischargeSlots,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_charge_discharge_slots.all_cids)

        self.inverter_charge_discharge_slot = inverter_charge_discharge_slot
        self.inverter_charge_discharge_slots = inverter_charge_discharge_slots

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.get(self.inverter_charge_discharge_slot.switch_cid)
        return value == "1" if value is not None else None

    async def async_turn_on(self, **kwargs: dict[str, any]) -> None:  # noqa: ARG002
        old_value = self._calculate_old_value()
        _LOGGER.info("Turn on '%s' (old_value: %s)", self.name, old_value)
        await self.coordinator.control(self.inverter_charge_discharge_slot.switch_cid, "1", old_value)

    async def async_turn_off(self, **kwargs: dict[str, any]) -> None:  # noqa: ARG002
        old_value = self._calculate_old_value()
        _LOGGER.info("Turn off '%s' (old_value: %s)", self.name, old_value)
        await self.coordinator.control(self.inverter_charge_discharge_slot.switch_cid, "0", old_value)

    def _calculate_old_value(self) -> str:
        slots = self.inverter_charge_discharge_slots
        data = self.coordinator.data

        slot_states = {
            slots.bit_charge_slot1: data.get(slots.charge_slot1.switch_cid) == "1",
            slots.bit_charge_slot2: data.get(slots.charge_slot2.switch_cid) == "1",
            slots.bit_charge_slot3: data.get(slots.charge_slot3.switch_cid) == "1",
            slots.bit_charge_slot4: data.get(slots.charge_slot4.switch_cid) == "1",
            slots.bit_charge_slot5: data.get(slots.charge_slot5.switch_cid) == "1",
            slots.bit_charge_slot6: data.get(slots.charge_slot6.switch_cid) == "1",
            slots.bit_discharge_slot1: data.get(slots.discharge_slot1.switch_cid) == "1",
            slots.bit_discharge_slot2: data.get(slots.discharge_slot2.switch_cid) == "1",
            slots.bit_discharge_slot3: data.get(slots.discharge_slot3.switch_cid) == "1",
            slots.bit_discharge_slot4: data.get(slots.discharge_slot4.switch_cid) == "1",
            slots.bit_discharge_slot5: data.get(slots.discharge_slot5.switch_cid) == "1",
            slots.bit_discharge_slot6: data.get(slots.discharge_slot6.switch_cid) == "1",
        }

        value = 0
        for bit_position, is_enabled in slot_states.items():
            if is_enabled:
                value |= 1 << bit_position

        return str(value)


class BatteryReserveSwitch(SolisCloudControlEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: SwitchEntityDescription,
        inverter_storage_mode: InverterStorageMode,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_storage_mode.cid)
        self.inverter_storage_mode = inverter_storage_mode

    @property
    def is_on(self) -> bool | None:
        value_str = self.coordinator.data.get(self.inverter_storage_mode.cid)
        value = safe_get_int_value(value_str)
        if value is None:
            return None

        return bool(value & (1 << self.inverter_storage_mode.bit_backup_mode))

    async def async_turn_on(self, **kwargs: any) -> None:  # noqa: ARG002
        await self._async_set_bit(True)

    async def async_turn_off(self, **kwargs: any) -> None:  # noqa: ARG002
        await self._async_set_bit(False)

    async def _async_set_bit(self, state: bool) -> None:
        value_str = self.coordinator.data.get(self.inverter_storage_mode.cid)
        value = safe_get_int_value(value_str)
        if value is None:
            return

        if state:
            value |= 1 << self.inverter_storage_mode.bit_backup_mode
        else:
            value &= ~(1 << self.inverter_storage_mode.bit_backup_mode)

        _LOGGER.info("Toggle '%s' (state: %s, value: %s)", self.name, state, value)
        await self.coordinator.control(self.inverter_storage_mode.cid, str(value))


class AllowGridChargingSwitch(SolisCloudControlEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: SwitchEntityDescription,
        inverter_storage_mode: InverterStorageMode,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_storage_mode.cid)
        self.inverter_storage_mode = inverter_storage_mode

    @property
    def is_on(self) -> bool | None:
        value_str = self.coordinator.data.get(self.inverter_storage_mode.cid)
        value = safe_get_int_value(value_str)
        if value is None:
            return None

        return bool(value & (1 << self.inverter_storage_mode.bit_grid_charging))

    async def async_turn_on(self, **kwargs: any) -> None:  # noqa: ARG002
        await self._async_set_bit(True)

    async def async_turn_off(self, **kwargs: any) -> None:  # noqa: ARG002
        await self._async_set_bit(False)

    async def _async_set_bit(self, state: bool) -> None:
        value_str = self.coordinator.data.get(self.inverter_storage_mode.cid)
        value = safe_get_int_value(value_str)
        if value is None:
            return

        if state:
            value |= 1 << self.inverter_storage_mode.bit_grid_charging
        else:
            value &= ~(1 << self.inverter_storage_mode.bit_grid_charging)

        _LOGGER.info("Toggle '%s' (state: %s, value: %s)", self.name, state, value)
        await self.coordinator.control(self.inverter_storage_mode.cid, str(value))
