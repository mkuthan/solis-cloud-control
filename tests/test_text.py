import pytest
from homeassistant.components.text import TextEntityDescription
from homeassistant.exceptions import HomeAssistantError

from custom_components.solis_cloud_control.text import (
    ChargeDischargeSettingsText,
    TimeSlotText,
)


@pytest.fixture
def time_slot_entity(mock_coordinator, any_inverter):
    return TimeSlotText(
        coordinator=mock_coordinator,
        entity_description=TextEntityDescription(
            key="slot1_charge_time",
            name="Slot1 Charge Time",
            icon="mdi:timer-plus-outline",
        ),
        charge_discharge_slot=any_inverter.charge_discharge_slots.charge_slot1,
    )


@pytest.fixture
def charge_discharge_settings_entity(mock_coordinator, any_inverter):
    return ChargeDischargeSettingsText(
        coordinator=mock_coordinator,
        entity_description=TextEntityDescription(
            key="charge_discharge_settings",
            name="Charge Discharge Settings",
        ),
        charge_discharge_settings=any_inverter.charge_discharge_settings,
    )


class TestTimeSlotText:
    def test_attributes(self, time_slot_entity):
        assert time_slot_entity.native_min == TimeSlotText._TEXT_LENGTH
        assert time_slot_entity.native_max == TimeSlotText._TEXT_LENGTH
        assert time_slot_entity.pattern == TimeSlotText._TEXT_PATTERN

    def test_native_value(self, time_slot_entity):
        time_slot_entity.coordinator.data = {time_slot_entity.charge_discharge_slot.time_cid: "10:00-12:00"}
        assert time_slot_entity.native_value == "10:00-12:00"

    def test_native_value_no_data(self, time_slot_entity):
        time_slot_entity.coordinator.data = {time_slot_entity.charge_discharge_slot.time_cid: None}
        assert time_slot_entity.native_value is None

    def test_native_value_invalid_format(self, time_slot_entity):
        time_slot_entity.coordinator.data = {time_slot_entity.charge_discharge_slot.time_cid: "00:01-2300:5000"}
        assert time_slot_entity.native_value is None

    async def test_async_set_value_valid(self, time_slot_entity):
        await time_slot_entity.async_set_value("09:00-17:00")
        time_slot_entity.coordinator.control.assert_awaited_once_with(
            time_slot_entity.charge_discharge_slot.time_cid, "09:00-17:00"
        )

    async def test_async_set_value_invalid(self, time_slot_entity):
        with pytest.raises(HomeAssistantError, match="Invalid 'Slot1 Charge Time': 25:00-26:00"):
            await time_slot_entity.async_set_value("25:00-26:00")


class TestChargeDischargeSettingsText:
    ANY_VALUE_VARIANT1 = "0,0,09:00,10:00,11:00,12:00,50,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00"
    ANY_VALUE_VARIANT2 = "0,0,09:00-10:00,11:00-12:00,50,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00"

    @pytest.mark.parametrize("test_value", [ANY_VALUE_VARIANT1, ANY_VALUE_VARIANT2])
    def test_native_value(self, charge_discharge_settings_entity, test_value):
        charge_discharge_settings_entity.coordinator.data = {
            charge_discharge_settings_entity.charge_discharge_settings.cid: test_value
        }
        assert charge_discharge_settings_entity.native_value == test_value

    def test_native_value_no_data(self, charge_discharge_settings_entity):
        charge_discharge_settings_entity.coordinator.data = {
            charge_discharge_settings_entity.charge_discharge_settings.cid: None
        }
        assert charge_discharge_settings_entity.native_value is None

    @pytest.mark.parametrize("test_value", [ANY_VALUE_VARIANT1, ANY_VALUE_VARIANT2])
    def test_extra_state_attributes(self, charge_discharge_settings_entity, test_value):
        charge_discharge_settings_entity.coordinator.data = {
            charge_discharge_settings_entity.charge_discharge_settings.cid: test_value
        }

        attributes = charge_discharge_settings_entity.extra_state_attributes

        assert attributes["slot1_charge_current"] == "0"
        assert attributes["slot1_discharge_current"] == "0"
        assert attributes["slot1_charge_time"] == "09:00-10:00"
        assert attributes["slot1_discharge_time"] == "11:00-12:00"

        assert attributes["slot2_charge_current"] == "50"
        assert attributes["slot2_discharge_current"] == "0"
        assert attributes["slot2_charge_time"] == "12:30-13:30"
        assert attributes["slot2_discharge_time"] == "14:30-15:30"

        assert attributes["slot3_charge_current"] == "0"
        assert attributes["slot3_discharge_current"] == "100"
        assert attributes["slot3_charge_time"] == "16:00-17:00"
        assert attributes["slot3_discharge_time"] == "18:00-19:00"

    def test_extra_state_attributes_no_data(self, charge_discharge_settings_entity):
        charge_discharge_settings_entity.coordinator.data = {
            charge_discharge_settings_entity.charge_discharge_settings.cid: None
        }

        attributes = charge_discharge_settings_entity.extra_state_attributes
        assert attributes == {}

    @pytest.mark.parametrize("test_value", [ANY_VALUE_VARIANT1, ANY_VALUE_VARIANT2])
    async def test_async_set_value_valid(self, charge_discharge_settings_entity, test_value):
        await charge_discharge_settings_entity.async_set_value(test_value)
        charge_discharge_settings_entity.coordinator.control.assert_awaited_once_with(
            charge_discharge_settings_entity.charge_discharge_settings.cid, test_value
        )

    @pytest.mark.parametrize(
        "invalid_value",
        [
            "X,0,09:00,10:00,11:00,12:00,50,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00",
            "0,X,09:00,10:00,11:00,12:00,50,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00",
            "0,0,25:00,10:00,11:00,12:00,50,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00",
            "0,0,09:00,25:00,11:00,12:00,50,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00",
            "0,0,09:00,10:00,25:00,12:00,50,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00",
            "0,0,09:00,10:00,11:00,25:00,50,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00",
            "",
        ],
    )
    async def test_async_set_value_invalid_variant1(self, charge_discharge_settings_entity, invalid_value):
        with pytest.raises(HomeAssistantError, match="Invalid 'Charge Discharge Settings'"):
            await charge_discharge_settings_entity.async_set_value(invalid_value)

    @pytest.mark.parametrize(
        "invalid_value",
        [
            "X,0,09:00-10:00,11:00-12:00,50,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00",
            "0,X,09:00-10:00,11:00-12:00,50,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00",
            "0,0,25:00-10:00,11:00-12:00,50,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00",
            "0,0,09:00-25:00,11:00-12:00,50,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00",
            "0,0,09:00-10:00,25:00-12:00,50,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00",
            "0,0,09:00-10:00,11:00-25:00,50,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00",
            "",
        ],
    )
    async def test_async_set_value_invalid_variant2(self, charge_discharge_settings_entity, invalid_value):
        with pytest.raises(HomeAssistantError, match="Invalid 'Charge Discharge Settings'"):
            await charge_discharge_settings_entity.async_set_value(invalid_value)
