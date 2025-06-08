import logging

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry
from custom_components.solis_cloud_control.inverters.inverter import (
    InverterChargeDischargeSlot,
    InverterChargeDischargeSlots,
    InverterOnOff,
    InverterStorageMode,  # Added import
)
from custom_components.solis_cloud_control.utils.safe_converters import safe_get_int_value  # Added import

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
                on_off=inverter.on_off,
            )
        )

    slots = inverter.charge_discharge_slots

    if slots is not None:
        tou_v2 = coordinator.data.get(slots.tou_v2_cid)

        if not slots.is_tou_v2_enabled(tou_v2):
            _LOGGER.info("Charge Discharge Slots not available, skip on/off entities creation")
        else:
            for i in range(1, slots.SLOTS_COUNT + 1):
                entities.append(
                    SlotSwitch(
                        coordinator=coordinator,
                        entity_description=SwitchEntityDescription(
                            key=f"slot{i}_charge_switch",
                            name=f"Slot{i} Charge",
                            icon="mdi:battery-plus-outline",
                        ),
                        charge_discharge_slot=slots.get_charge_slot(i),
                        charge_discharge_slots=slots,
                    )
                )
                entities.append(
                    SlotSwitch(
                        coordinator=coordinator,
                        entity_description=SwitchEntityDescription(
                            key=f"slot{i}_discharge_switch",
                            name=f"Slot{i} Discharge",
                            icon="mdi:battery-minus-outline",
                        ),
                        charge_discharge_slot=slots.get_discharge_slot(i),
                        charge_discharge_slots=slots,
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
                storage_mode=inverter.storage_mode,
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
                storage_mode=inverter.storage_mode,
            )
        )

    async_add_entities(entities)


class OnOffSwitch(SolisCloudControlEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: SwitchEntityDescription,
        on_off: InverterOnOff,
    ) -> None:
        super().__init__(coordinator, entity_description, [on_off.on_cid, on_off.off_cid])
        self.on_off = on_off

    @property
    def assumed_state(self) -> bool:
        on_value = self.coordinator.data.get(self.on_off.on_cid)
        off_value = self.coordinator.data.get(self.on_off.off_cid)

        same_values = on_value == off_value
        valid_values = self.on_off.is_valid_value(on_value) and self.on_off.is_valid_value(off_value)

        return not (same_values and valid_values)

    @property
    def is_on(self) -> bool | None:
        on_value = self.coordinator.data.get(self.on_off.on_cid)
        off_value = self.coordinator.data.get(self.on_off.off_cid)

        same_values = on_value == off_value
        valid_values = self.on_off.is_valid_value(on_value) and self.on_off.is_valid_value(off_value)

        if same_values and valid_values:
            return on_value == self.on_off.on_value

        return None

    async def async_turn_on(self, **kwargs: dict[str, any]) -> None:  # noqa: ARG002
        _LOGGER.info("Turning on inverter")
        if self.assumed_state:
            await self.coordinator.control_no_check(self.on_off.on_cid, self.on_off.on_value)
        else:
            await self.coordinator.control(self.on_off.on_cid, self.on_off.on_value)

    async def async_turn_off(self, **kwargs: dict[str, any]) -> None:  # noqa: ARG002
        _LOGGER.info("Turning off inverter")
        if self.assumed_state:
            await self.coordinator.control_no_check(self.on_off.off_cid, self.on_off.off_value)
        else:
            await self.coordinator.control(self.on_off.off_cid, self.on_off.off_value)


class SlotSwitch(SolisCloudControlEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: SwitchEntityDescription,
        charge_discharge_slot: InverterChargeDischargeSlot,
        charge_discharge_slots: InverterChargeDischargeSlots,
    ) -> None:
        super().__init__(coordinator, entity_description, charge_discharge_slots.all_cids)

        self.charge_discharge_slot = charge_discharge_slot
        self.charge_discharge_slots = charge_discharge_slots

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.get(self.charge_discharge_slot.switch_cid)
        return value == "1" if value is not None else None

    async def async_turn_on(self, **kwargs: dict[str, any]) -> None:  # noqa: ARG002
        old_value = self._calculate_old_value()
        _LOGGER.info("Turning on slot (old_value: %s)", old_value)
        await self.coordinator.control(self.charge_discharge_slot.switch_cid, "1", old_value)

    async def async_turn_off(self, **kwargs: dict[str, any]) -> None:  # noqa: ARG002
        old_value = self._calculate_old_value()
        _LOGGER.info("Turning off slot (old_value: %s)", old_value)
        await self.coordinator.control(self.charge_discharge_slot.switch_cid, "0", old_value)

    def _calculate_old_value(self) -> str:
        slots = self.charge_discharge_slots
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
        storage_mode: InverterStorageMode,
    ) -> None:
        super().__init__(coordinator, entity_description, storage_mode.cid)
        self.storage_mode = storage_mode

    @property
    def is_on(self) -> bool | None:
        value_str = self.coordinator.data.get(self.storage_mode.cid)
        value = safe_get_int_value(value_str)
        if value is None:
            return None

        return bool(value & (1 << self.storage_mode.bit_backup_mode))

    async def async_turn_on(self, **kwargs: any) -> None:  # noqa: ARG002
        await self._async_set_bit(True)

    async def async_turn_off(self, **kwargs: any) -> None:  # noqa: ARG002
        await self._async_set_bit(False)

    async def _async_set_bit(self, state: bool) -> None:
        value_str = self.coordinator.data.get(self.storage_mode.cid)
        value = safe_get_int_value(value_str)
        if value is None:
            return

        if state:
            value |= 1 << self.storage_mode.bit_backup_mode
        else:
            value &= ~(1 << self.storage_mode.bit_backup_mode)

        _LOGGER.info("Setting battery reserve to %s (value: %s)", state, value)
        await self.coordinator.control(self.storage_mode.cid, str(value))


class AllowGridChargingSwitch(SolisCloudControlEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: SwitchEntityDescription,
        storage_mode: InverterStorageMode,
    ) -> None:
        super().__init__(coordinator, entity_description, storage_mode.cid)
        self.storage_mode = storage_mode

    @property
    def is_on(self) -> bool | None:
        value_str = self.coordinator.data.get(self.storage_mode.cid)
        value = safe_get_int_value(value_str)
        if value is None:
            return None

        return bool(value & (1 << self.storage_mode.bit_grid_charging))

    async def async_turn_on(self, **kwargs: any) -> None:  # noqa: ARG002
        await self._async_set_bit(True)

    async def async_turn_off(self, **kwargs: any) -> None:  # noqa: ARG002
        await self._async_set_bit(False)

    async def _async_set_bit(self, state: bool) -> None:
        value_str = self.coordinator.data.get(self.storage_mode.cid)
        value = safe_get_int_value(value_str)
        if value is None:
            return

        if state:
            value |= 1 << self.storage_mode.bit_grid_charging
        else:
            value &= ~(1 << self.storage_mode.bit_grid_charging)

        _LOGGER.info("Setting allow grid charging to %s (value: %s)", state, value)
        await self.coordinator.control(self.storage_mode.cid, str(value))
