import logging

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry
from custom_components.solis_cloud_control.inverter import InverterChargeDischargeSlot, InverterChargeDischargeSlots

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
            SlotSwitch(
                coordinator=coordinator,
                entity_description=SwitchEntityDescription(
                    key="slot1_charge_switch",
                    name="Slot1 Charge",
                    icon="mdi:battery-plus-outline",
                ),
                charge_discharge_slot=inverter.charge_discharge_slots.charge_slot1,
                charge_discharge_slots=inverter.charge_discharge_slots,
            )
        )
        entities.append(
            SlotSwitch(
                coordinator=coordinator,
                entity_description=SwitchEntityDescription(
                    key="slot1_discharge_switch",
                    name="Slot1 Discharge",
                    icon="mdi:battery-minus-outline",
                ),
                charge_discharge_slot=inverter.charge_discharge_slots.discharge_slot1,
                charge_discharge_slots=inverter.charge_discharge_slots,
            )
        )

    async_add_entities(entities)


class SlotSwitch(SolisCloudControlEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: SwitchEntityDescription,
        charge_discharge_slot: InverterChargeDischargeSlot,
        charge_discharge_slots: InverterChargeDischargeSlots,
    ) -> None:
        super().__init__(coordinator, entity_description)

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
        slot_states = {
            self.charge_discharge_slots.bit_charge_slot1: self.coordinator.data.get(
                self.charge_discharge_slots.charge_slot1.switch_cid
            )
            == "1",
            self.charge_discharge_slots.bit_charge_slot2: self.coordinator.data.get(
                self.charge_discharge_slots.charge_slot2.switch_cid
            )
            == "1",
            self.charge_discharge_slots.bit_charge_slot3: self.coordinator.data.get(
                self.charge_discharge_slots.charge_slot3.switch_cid
            )
            == "1",
            self.charge_discharge_slots.bit_charge_slot4: self.coordinator.data.get(
                self.charge_discharge_slots.charge_slot4.switch_cid
            )
            == "1",
            self.charge_discharge_slots.bit_charge_slot5: self.coordinator.data.get(
                self.charge_discharge_slots.charge_slot5.switch_cid
            )
            == "1",
            self.charge_discharge_slots.bit_charge_slot6: self.coordinator.data.get(
                self.charge_discharge_slots.charge_slot6.switch_cid
            )
            == "1",
            self.charge_discharge_slots.bit_discharge_slot1: self.coordinator.data.get(
                self.charge_discharge_slots.discharge_slot1.switch_cid
            )
            == "1",
            self.charge_discharge_slots.bit_discharge_slot2: self.coordinator.data.get(
                self.charge_discharge_slots.discharge_slot2.switch_cid
            )
            == "1",
            self.charge_discharge_slots.bit_discharge_slot3: self.coordinator.data.get(
                self.charge_discharge_slots.discharge_slot3.switch_cid
            )
            == "1",
            self.charge_discharge_slots.bit_discharge_slot4: self.coordinator.data.get(
                self.charge_discharge_slots.discharge_slot4.switch_cid
            )
            == "1",
            self.charge_discharge_slots.bit_discharge_slot5: self.coordinator.data.get(
                self.charge_discharge_slots.discharge_slot5.switch_cid
            )
            == "1",
            self.charge_discharge_slots.bit_discharge_slot6: self.coordinator.data.get(
                self.charge_discharge_slots.discharge_slot6.switch_cid
            )
            == "1",
        }

        value = 0
        for bit_position, is_enabled in slot_states.items():
            if is_enabled:
                value |= 1 << bit_position

        return str(value)
