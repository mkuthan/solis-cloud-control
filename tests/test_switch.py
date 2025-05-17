import pytest
from homeassistant.components.switch import SwitchEntityDescription

from custom_components.solis_cloud_control.switch import OnOffSwitch, SlotSwitch


@pytest.fixture
def on_off_switch(mock_coordinator, any_inverter):
    return OnOffSwitch(
        coordinator=mock_coordinator,
        entity_description=SwitchEntityDescription(
            key="on_off_switch",
            name="Inverter On/Off",
            icon="mdi:power",
        ),
        on_off=any_inverter.on_off,
    )


class TestOnOffSwitch:
    def test_init(self, on_off_switch):
        assert on_off_switch.is_on is True
        assert on_off_switch.assumed_state is True

    async def test_turn_on(self, on_off_switch):
        await on_off_switch.async_turn_on()
        on_off_switch.coordinator.control.assert_awaited_once_with(
            on_off_switch.on_off.on_cid, on_off_switch.on_off.on_value
        )
        assert on_off_switch.is_on is True

    async def test_turn_off(self, on_off_switch):
        await on_off_switch.async_turn_off()
        on_off_switch.coordinator.control.assert_awaited_once_with(
            on_off_switch.on_off.off_cid, on_off_switch.on_off.off_value
        )
        assert on_off_switch.is_on is False


@pytest.fixture
def slot_switch(mock_coordinator, any_inverter):
    return SlotSwitch(
        coordinator=mock_coordinator,
        entity_description=SwitchEntityDescription(
            key="slot1_charge_switch",
            name="Slot1 Charge",
            icon="mdi:battery-plus-outline",
        ),
        charge_discharge_slot=any_inverter.charge_discharge_slots.charge_slot1,
        charge_discharge_slots=any_inverter.charge_discharge_slots,
    )


class TestSlotSwitch:
    async def test_is_on_when_none(self, slot_switch):
        slot_switch.coordinator.data = {slot_switch.charge_discharge_slot.switch_cid: None}
        assert slot_switch.is_on is None

    async def test_is_on_when_on(self, slot_switch):
        slot_switch.coordinator.data = {slot_switch.charge_discharge_slot.switch_cid: "1"}
        assert slot_switch.is_on is True

    async def test_is_on_when_off(self, slot_switch):
        slot_switch.coordinator.data = {slot_switch.charge_discharge_slot.switch_cid: "0"}
        assert slot_switch.is_on is False

    async def test_calculate_old_value_with_data(self, slot_switch):
        slot_switch.coordinator.data = {
            slot_switch.charge_discharge_slots.charge_slot1.switch_cid: "1",
            slot_switch.charge_discharge_slots.charge_slot2.switch_cid: "1",
            slot_switch.charge_discharge_slots.discharge_slot1.switch_cid: "0",
        }
        # First two bits should be set (positions 0 and 1)
        assert slot_switch._calculate_old_value() == "3"

    async def test_turn_on(self, slot_switch):
        slot_switch.coordinator.data = {slot_switch.charge_discharge_slot.switch_cid: "0"}
        await slot_switch.async_turn_on()
        slot_switch.coordinator.control.assert_awaited_once_with(slot_switch.charge_discharge_slot.switch_cid, "1", "0")

    async def test_turn_off(self, slot_switch):
        slot_switch.coordinator.data = {slot_switch.charge_discharge_slot.switch_cid: "1"}
        await slot_switch.async_turn_off()
        slot_switch.coordinator.control.assert_awaited_once_with(slot_switch.charge_discharge_slot.switch_cid, "0", "1")
