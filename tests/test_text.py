import pytest
from homeassistant.components.text import TextEntityDescription

from custom_components.solis_cloud_control.text import (
    TimeSlotV1Text,
    TimeSlotV2Text,
)


@pytest.fixture
def time_slot_v1_charge_entity(mock_coordinator, any_inverter):
    return TimeSlotV1Text(
        coordinator=mock_coordinator,
        entity_description=TextEntityDescription(key="any_key", name="any name"),
        inverter_charge_discharge_settings=any_inverter.charge_discharge_settings,
        slot_number=1,
        slot_type="charge",
    )


@pytest.fixture
def time_slot_v1_discharge_entity(mock_coordinator, any_inverter):
    return TimeSlotV1Text(
        coordinator=mock_coordinator,
        entity_description=TextEntityDescription(key="any_key", name="any name"),
        inverter_charge_discharge_settings=any_inverter.charge_discharge_settings,
        slot_number=1,
        slot_type="discharge",
    )


class TestTimeSlotV1Text:
    VARIANT1_VALUE = "0,0,09:00,10:00,11:00,12:00,50,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00"
    VARIANT2_VALUE = "0,0,09:00-10:00,11:00-12:00,50,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00"

    def test_attributes(self, time_slot_v1_charge_entity):
        assert time_slot_v1_charge_entity.native_min == TimeSlotV1Text._TEXT_LENGTH
        assert time_slot_v1_charge_entity.native_max == TimeSlotV1Text._TEXT_LENGTH
        assert time_slot_v1_charge_entity.pattern == TimeSlotV1Text._TEXT_PATTERN

    @pytest.mark.parametrize("value", [VARIANT1_VALUE, VARIANT2_VALUE])
    def test_native_value_charge_slot(self, time_slot_v1_charge_entity, value):
        time_slot_v1_charge_entity.coordinator.data = {
            time_slot_v1_charge_entity.inverter_charge_discharge_settings.cid: value
        }
        assert time_slot_v1_charge_entity.native_value == "09:00-10:00"

    @pytest.mark.parametrize("value", [VARIANT1_VALUE, VARIANT2_VALUE])
    def test_native_value_discharge_slot(self, time_slot_v1_discharge_entity, value):
        time_slot_v1_discharge_entity.coordinator.data = {
            time_slot_v1_discharge_entity.inverter_charge_discharge_settings.cid: value
        }
        assert time_slot_v1_discharge_entity.native_value == "11:00-12:00"

    def test_native_value_no_data(self, time_slot_v1_charge_entity):
        time_slot_v1_charge_entity.coordinator.data = {
            time_slot_v1_charge_entity.inverter_charge_discharge_settings.cid: None
        }
        assert time_slot_v1_charge_entity.native_value is None

    async def test_async_set_value_variant1_charge_slot(self, time_slot_v1_charge_entity):
        time_slot_v1_charge_entity.coordinator.data = {
            time_slot_v1_charge_entity.inverter_charge_discharge_settings.cid: self.VARIANT1_VALUE
        }
        await time_slot_v1_charge_entity.async_set_value("23:00-23:59")
        expected_value = "0,0,23:00,23:59,11:00,12:00,50,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00"
        time_slot_v1_charge_entity.coordinator.control.assert_awaited_once_with(
            time_slot_v1_charge_entity.inverter_charge_discharge_settings.cid, expected_value
        )

    async def test_async_set_value_variant1_discharge(self, time_slot_v1_discharge_entity):
        time_slot_v1_discharge_entity.coordinator.data = {
            time_slot_v1_discharge_entity.inverter_charge_discharge_settings.cid: self.VARIANT1_VALUE
        }
        await time_slot_v1_discharge_entity.async_set_value("23:00-23:59")
        expected_value = "0,0,09:00,10:00,23:00,23:59,50,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00"
        time_slot_v1_discharge_entity.coordinator.control.assert_awaited_once_with(
            time_slot_v1_discharge_entity.inverter_charge_discharge_settings.cid, expected_value
        )

    async def test_async_set_value_variant2_charge(self, time_slot_v1_charge_entity):
        time_slot_v1_charge_entity.coordinator.data = {
            time_slot_v1_charge_entity.inverter_charge_discharge_settings.cid: self.VARIANT2_VALUE
        }
        await time_slot_v1_charge_entity.async_set_value("23:00-23:59")
        expected_value = "0,0,23:00-23:59,11:00-12:00,50,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00"
        time_slot_v1_charge_entity.coordinator.control.assert_awaited_once_with(
            time_slot_v1_charge_entity.inverter_charge_discharge_settings.cid, expected_value
        )

    async def test_async_set_value_variant2_discharge(self, time_slot_v1_discharge_entity):
        time_slot_v1_discharge_entity.coordinator.data = {
            time_slot_v1_discharge_entity.inverter_charge_discharge_settings.cid: self.VARIANT2_VALUE
        }
        await time_slot_v1_discharge_entity.async_set_value("23:00-23:59")
        expected_value = "0,0,09:00-10:00,23:00-23:59,50,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00"
        time_slot_v1_discharge_entity.coordinator.control.assert_awaited_once_with(
            time_slot_v1_discharge_entity.inverter_charge_discharge_settings.cid, expected_value
        )

    async def test_async_set_value_no_current_settings(self, time_slot_v1_charge_entity):
        time_slot_v1_charge_entity.coordinator.data = {
            time_slot_v1_charge_entity.inverter_charge_discharge_settings.cid: None
        }
        await time_slot_v1_charge_entity.async_set_value("23:00-23:59")
        time_slot_v1_charge_entity.coordinator.control.assert_not_called()

    async def test_async_set_value_invalid_settings_format(self, time_slot_v1_charge_entity):
        invalid_format = "invalid format"
        time_slot_v1_charge_entity.coordinator.data = {
            time_slot_v1_charge_entity.inverter_charge_discharge_settings.cid: invalid_format
        }
        await time_slot_v1_charge_entity.async_set_value("23:00-23:59")
        time_slot_v1_charge_entity.coordinator.control.assert_not_called()


@pytest.fixture
def time_slot_v2_entity(mock_coordinator, any_inverter):
    return TimeSlotV2Text(
        coordinator=mock_coordinator,
        entity_description=TextEntityDescription(key="any_key", name="any name"),
        inverter_charge_discharge_slot=any_inverter.charge_discharge_slots.charge_slot1,
    )


class TestTimeSlotV2Text:
    def test_attributes(self, time_slot_v2_entity):
        assert time_slot_v2_entity.native_min == TimeSlotV2Text._TEXT_LENGTH
        assert time_slot_v2_entity.native_max == TimeSlotV2Text._TEXT_LENGTH
        assert time_slot_v2_entity.pattern == TimeSlotV2Text._TEXT_PATTERN

    def test_native_value(self, time_slot_v2_entity):
        time_slot_v2_entity.coordinator.data = {
            time_slot_v2_entity.inverter_charge_discharge_slot.time_cid: "10:00-12:00"
        }
        assert time_slot_v2_entity.native_value == "10:00-12:00"

    def test_native_value_no_data(self, time_slot_v2_entity):
        time_slot_v2_entity.coordinator.data = {time_slot_v2_entity.inverter_charge_discharge_slot.time_cid: None}
        assert time_slot_v2_entity.native_value is None

    async def test_async_set_value_valid(self, time_slot_v2_entity):
        await time_slot_v2_entity.async_set_value("09:00-17:00")
        time_slot_v2_entity.coordinator.control.assert_awaited_once_with(
            time_slot_v2_entity.inverter_charge_discharge_slot.time_cid, "09:00-17:00"
        )
