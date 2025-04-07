import pytest
from homeassistant.components.switch import SwitchEntityDescription

from custom_components.solis_cloud_control.const import (
    CID_CHARGE_SLOT1_SWITCH,
    CID_CHARGE_SLOT2_SWITCH,
    CID_DISCHARGE_SLOT1_SWITCH,
)
from custom_components.solis_cloud_control.switch import SlotSwitch


@pytest.fixture
def slot_switch(mock_coordinator):
    mock_coordinator.data = {CID_CHARGE_SLOT1_SWITCH: "0"}

    entity = SlotSwitch(
        coordinator=mock_coordinator,
        entity_description=SwitchEntityDescription(
            key="slot1_charge_switch",
            name="Slot1 Charge",
            icon="mdi:battery-plus-outline",
        ),
        cid=CID_CHARGE_SLOT1_SWITCH,
    )
    return entity


class TestSlotSwitch:
    async def test_is_on_when_none(self, slot_switch):
        slot_switch.coordinator.data = None
        assert slot_switch.is_on is None

    async def test_is_on_when_on(self, slot_switch):
        slot_switch.coordinator.data = {CID_CHARGE_SLOT1_SWITCH: "1"}
        assert slot_switch.is_on is True

    async def test_is_on_when_off(self, slot_switch):
        slot_switch.coordinator.data = {CID_CHARGE_SLOT1_SWITCH: "0"}
        assert slot_switch.is_on is False

    async def test_calculate_old_value_no_data(self, slot_switch):
        slot_switch.coordinator.data = None
        assert slot_switch._calculate_old_value() == "0"

    async def test_calculate_old_value_with_data(self, slot_switch):
        slot_switch.coordinator.data = {
            CID_CHARGE_SLOT1_SWITCH: "1",
            CID_CHARGE_SLOT2_SWITCH: "1",
            CID_DISCHARGE_SLOT1_SWITCH: "0",
        }
        # First two bits should be set (positions 0 and 1)
        assert slot_switch._calculate_old_value() == "3"

    async def test_turn_on(self, slot_switch):
        slot_switch.coordinator.data = {CID_CHARGE_SLOT1_SWITCH: "0"}
        await slot_switch.async_turn_on()
        slot_switch.coordinator.control.assert_awaited_once_with(CID_CHARGE_SLOT1_SWITCH, "1", "0")

    async def test_turn_off(self, slot_switch):
        slot_switch.coordinator.data = {CID_CHARGE_SLOT1_SWITCH: "1"}
        await slot_switch.async_turn_off()
        slot_switch.coordinator.control.assert_awaited_once_with(CID_CHARGE_SLOT1_SWITCH, "0", "1")
