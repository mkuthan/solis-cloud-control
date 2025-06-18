import pytest
from homeassistant.components.switch import SwitchEntityDescription

from custom_components.solis_cloud_control.switch import (
    AllowGridChargingSwitch,
    BatteryReserveSwitch,
    OnOffSwitch,
    SlotV2Switch,
)


@pytest.fixture
def on_off_switch(mock_coordinator, any_inverter):
    return OnOffSwitch(
        coordinator=mock_coordinator,
        entity_description=SwitchEntityDescription(key="any_key", name="any name"),
        inverter_on_off=any_inverter.on_off,
    )


class TestOnOffSwitch:
    def test_is_on_when_valid_on_values(self, on_off_switch):
        on_off_switch.coordinator.data = {
            on_off_switch.inverter_on_off.on_cid: "190",
            on_off_switch.inverter_on_off.off_cid: "190",
        }
        assert on_off_switch.is_on is True
        assert on_off_switch.assumed_state is False

    def test_is_on_when_valid_off_values(self, on_off_switch):
        on_off_switch.coordinator.data = {
            on_off_switch.inverter_on_off.on_cid: "222",
            on_off_switch.inverter_on_off.off_cid: "222",
        }
        assert on_off_switch.is_on is False
        assert on_off_switch.assumed_state is False

    def test_is_on_when_mixed_valid_values(self, on_off_switch):
        on_off_switch.coordinator.data = {
            on_off_switch.inverter_on_off.on_cid: "190",
            on_off_switch.inverter_on_off.off_cid: "222",
        }
        assert on_off_switch.is_on is None
        assert on_off_switch.assumed_state is True

    def test_is_on_when_invalid_values(self, on_off_switch):
        on_off_switch.coordinator.data = {
            on_off_switch.inverter_on_off.on_cid: "0",
            on_off_switch.inverter_on_off.off_cid: "0",
        }
        assert on_off_switch.is_on is None
        assert on_off_switch.assumed_state is True

    async def test_turn_on_with_assumed_state(self, on_off_switch):
        on_off_switch.coordinator.data = {
            on_off_switch.inverter_on_off.on_cid: "0",
            on_off_switch.inverter_on_off.off_cid: "0",
        }
        await on_off_switch.async_turn_on()
        on_off_switch.coordinator.control_no_check.assert_awaited_once_with(
            on_off_switch.inverter_on_off.on_cid, on_off_switch.inverter_on_off.on_value
        )

    async def test_turn_on_with_valid_state(self, on_off_switch):
        on_off_switch.coordinator.data = {
            on_off_switch.inverter_on_off.on_cid: "222",
            on_off_switch.inverter_on_off.off_cid: "222",
        }
        await on_off_switch.async_turn_on()
        on_off_switch.coordinator.control.assert_awaited_once_with(
            on_off_switch.inverter_on_off.on_cid, on_off_switch.inverter_on_off.on_value
        )

    async def test_turn_off_with_assumed_state(self, on_off_switch):
        on_off_switch.coordinator.data = {
            on_off_switch.inverter_on_off.on_cid: "0",
            on_off_switch.inverter_on_off.off_cid: "0",
        }
        await on_off_switch.async_turn_off()
        on_off_switch.coordinator.control_no_check.assert_awaited_once_with(
            on_off_switch.inverter_on_off.off_cid, on_off_switch.inverter_on_off.off_value
        )

    async def test_turn_off_with_valid_state(self, on_off_switch):
        on_off_switch.coordinator.data = {
            on_off_switch.inverter_on_off.on_cid: "190",
            on_off_switch.inverter_on_off.off_cid: "190",
        }
        await on_off_switch.async_turn_off()
        on_off_switch.coordinator.control.assert_awaited_once_with(
            on_off_switch.inverter_on_off.off_cid, on_off_switch.inverter_on_off.off_value
        )


@pytest.fixture
def slot_switch(mock_coordinator, any_inverter):
    return SlotV2Switch(
        coordinator=mock_coordinator,
        entity_description=SwitchEntityDescription(key="any_key", name="any name"),
        inverter_charge_discharge_slot=any_inverter.charge_discharge_slots.charge_slot1,
        inverter_charge_discharge_slots=any_inverter.charge_discharge_slots,
    )


class TestSlotSwitch:
    async def test_is_on_when_none(self, slot_switch):
        slot_switch.coordinator.data = {slot_switch.inverter_charge_discharge_slot.switch_cid: None}
        assert slot_switch.is_on is None

    async def test_is_on_when_on(self, slot_switch):
        slot_switch.coordinator.data = {slot_switch.inverter_charge_discharge_slot.switch_cid: "1"}
        assert slot_switch.is_on is True

    async def test_is_on_when_off(self, slot_switch):
        slot_switch.coordinator.data = {slot_switch.inverter_charge_discharge_slot.switch_cid: "0"}
        assert slot_switch.is_on is False

    async def test_calculate_old_value_with_data(self, slot_switch):
        slot_switch.coordinator.data = {
            slot_switch.inverter_charge_discharge_slots.charge_slot1.switch_cid: "1",
            slot_switch.inverter_charge_discharge_slots.charge_slot2.switch_cid: "1",
            slot_switch.inverter_charge_discharge_slots.discharge_slot1.switch_cid: "0",
        }
        # First two bits should be set (positions 0 and 1)
        assert slot_switch._calculate_old_value() == "3"

    async def test_turn_on(self, slot_switch):
        slot_switch.coordinator.data = {slot_switch.inverter_charge_discharge_slot.switch_cid: "0"}
        await slot_switch.async_turn_on()
        slot_switch.coordinator.control.assert_awaited_once_with(
            slot_switch.inverter_charge_discharge_slot.switch_cid, "1", "0"
        )

    async def test_turn_off(self, slot_switch):
        slot_switch.coordinator.data = {slot_switch.inverter_charge_discharge_slot.switch_cid: "1"}
        await slot_switch.async_turn_off()
        slot_switch.coordinator.control.assert_awaited_once_with(
            slot_switch.inverter_charge_discharge_slot.switch_cid, "0", "1"
        )


@pytest.fixture
def battery_reserve_switch(mock_coordinator, any_inverter):
    return BatteryReserveSwitch(
        coordinator=mock_coordinator,
        entity_description=SwitchEntityDescription(key="any_key", name="any name"),
        inverter_storage_mode=any_inverter.storage_mode,
    )


class TestBatteryReserveSwitch:
    def test_is_on_when_none(self, battery_reserve_switch):
        battery_reserve_switch.coordinator.data = {battery_reserve_switch.inverter_storage_mode.cid: None}
        assert battery_reserve_switch.is_on is None

    def test_is_on_when_on(self, battery_reserve_switch):
        bit = battery_reserve_switch.inverter_storage_mode.bit_backup_mode
        battery_reserve_switch.coordinator.data = {battery_reserve_switch.inverter_storage_mode.cid: str(1 << bit)}
        assert battery_reserve_switch.is_on is True

    def test_is_on_when_off(self, battery_reserve_switch):
        battery_reserve_switch.coordinator.data = {battery_reserve_switch.inverter_storage_mode.cid: str(0)}
        assert battery_reserve_switch.is_on is False

    async def test_turn_on(self, battery_reserve_switch):
        bit = battery_reserve_switch.inverter_storage_mode.bit_backup_mode
        battery_reserve_switch.coordinator.data = {battery_reserve_switch.inverter_storage_mode.cid: str(0)}
        await battery_reserve_switch.async_turn_on()
        battery_reserve_switch.coordinator.control.assert_awaited_once_with(
            battery_reserve_switch.inverter_storage_mode.cid, str(1 << bit)
        )

    async def test_turn_off(self, battery_reserve_switch):
        bit = battery_reserve_switch.inverter_storage_mode.bit_backup_mode
        battery_reserve_switch.coordinator.data = {battery_reserve_switch.inverter_storage_mode.cid: str(1 << bit)}
        await battery_reserve_switch.async_turn_off()
        battery_reserve_switch.coordinator.control.assert_awaited_once_with(
            battery_reserve_switch.inverter_storage_mode.cid, str(0)
        )

    @pytest.mark.parametrize(
        "initial_value",
        [
            "not a number",
            None,
        ],
    )
    async def test_async_turn_on_off_invalid_initial(self, battery_reserve_switch, initial_value):
        battery_reserve_switch.coordinator.data = {battery_reserve_switch.inverter_storage_mode.cid: initial_value}
        await battery_reserve_switch.async_turn_on()
        await battery_reserve_switch.async_turn_off()
        battery_reserve_switch.coordinator.control.assert_not_awaited()


@pytest.fixture
def allow_grid_charging_switch(mock_coordinator, any_inverter):
    return AllowGridChargingSwitch(
        coordinator=mock_coordinator,
        entity_description=SwitchEntityDescription(key="any_key", name="any name"),
        inverter_storage_mode=any_inverter.storage_mode,
    )


class TestAllowGridChargingSwitch:
    def test_is_on_when_none(self, allow_grid_charging_switch):
        allow_grid_charging_switch.coordinator.data = {allow_grid_charging_switch.inverter_storage_mode.cid: None}
        assert allow_grid_charging_switch.is_on is None

    def test_is_on_when_on(self, allow_grid_charging_switch):
        bit = allow_grid_charging_switch.inverter_storage_mode.bit_grid_charging
        allow_grid_charging_switch.coordinator.data = {
            allow_grid_charging_switch.inverter_storage_mode.cid: str(1 << bit)
        }
        assert allow_grid_charging_switch.is_on is True

    def test_is_on_when_off(self, allow_grid_charging_switch):
        allow_grid_charging_switch.coordinator.data = {allow_grid_charging_switch.inverter_storage_mode.cid: str(0)}
        assert allow_grid_charging_switch.is_on is False

    async def test_turn_on(self, allow_grid_charging_switch):
        bit = allow_grid_charging_switch.inverter_storage_mode.bit_grid_charging
        allow_grid_charging_switch.coordinator.data = {allow_grid_charging_switch.inverter_storage_mode.cid: str(0)}
        await allow_grid_charging_switch.async_turn_on()
        allow_grid_charging_switch.coordinator.control.assert_awaited_once_with(
            allow_grid_charging_switch.inverter_storage_mode.cid, str(1 << bit)
        )

    async def test_turn_off(self, allow_grid_charging_switch):
        bit = allow_grid_charging_switch.inverter_storage_mode.bit_grid_charging
        allow_grid_charging_switch.coordinator.data = {
            allow_grid_charging_switch.inverter_storage_mode.cid: str(1 << bit)
        }
        await allow_grid_charging_switch.async_turn_off()
        allow_grid_charging_switch.coordinator.control.assert_awaited_once_with(
            allow_grid_charging_switch.inverter_storage_mode.cid, str(0)
        )

    @pytest.mark.parametrize(
        "initial_value",
        [
            "not a number",
            None,
        ],
    )
    async def test_async_turn_on_off_invalid_initial(self, allow_grid_charging_switch, initial_value):
        allow_grid_charging_switch.coordinator.data = {
            allow_grid_charging_switch.inverter_storage_mode.cid: initial_value
        }
        await allow_grid_charging_switch.async_turn_on()
        await allow_grid_charging_switch.async_turn_off()
        allow_grid_charging_switch.coordinator.control.assert_not_awaited()
