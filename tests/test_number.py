from dataclasses import replace

import pytest
from homeassistant.components.number import NumberEntityDescription
from homeassistant.const import PERCENTAGE, UnitOfElectricCurrent, UnitOfPower

from custom_components.solis_cloud_control.number import (
    BatteryCurrentV1,
    BatteryCurrentV2,
    BatterySocV2,
    MaxExportPower,
    MaxOutputPower,
    PowerLimit,
)


@pytest.fixture
def battery_current_v1_charge_entity(mock_coordinator, any_inverter):
    return BatteryCurrentV1(
        coordinator=mock_coordinator,
        entity_description=NumberEntityDescription(key="any_key", name="any name"),
        inverter_charge_discharge_settings=any_inverter.charge_discharge_settings,
        inverter_battery_max_charge_discharge_current=any_inverter.battery_max_charge_current,
        slot_number=1,
        slot_type="charge",
    )


@pytest.fixture
def battery_current_v1_discharge_entity(mock_coordinator, any_inverter):
    return BatteryCurrentV1(
        coordinator=mock_coordinator,
        entity_description=NumberEntityDescription(key="any_key", name="any name"),
        inverter_charge_discharge_settings=any_inverter.charge_discharge_settings,
        inverter_battery_max_charge_discharge_current=any_inverter.battery_max_charge_current,
        slot_number=1,
        slot_type="discharge",
    )


class TestBatteryCurrentV1:
    VARIANT1_VALUE = "50,0,09:00,10:00,11:00,12:00,0,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00"
    VARIANT2_VALUE = "50,0,09:00-10:00,11:00-12:00,0,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00"

    def test_attributes(self, battery_current_v1_charge_entity):
        inverter_charge_discharge_settings = battery_current_v1_charge_entity.inverter_charge_discharge_settings
        assert battery_current_v1_charge_entity.native_min_value == inverter_charge_discharge_settings.current_min_value
        assert battery_current_v1_charge_entity.native_max_value == inverter_charge_discharge_settings.current_max_value
        assert battery_current_v1_charge_entity.native_step == inverter_charge_discharge_settings.current_step
        assert battery_current_v1_charge_entity.native_unit_of_measurement == UnitOfElectricCurrent.AMPERE

    def test_native_max_value(self, battery_current_v1_charge_entity):
        battery_current_v1_charge_entity.coordinator.data = {
            battery_current_v1_charge_entity.inverter_battery_max_charge_discharge_current.cid: "50"
        }
        assert battery_current_v1_charge_entity.native_max_value == 50

    @pytest.mark.parametrize("value", [VARIANT1_VALUE, VARIANT2_VALUE])
    def test_native_value_charge_current(self, battery_current_v1_charge_entity, value):
        battery_current_v1_charge_entity.coordinator.data = {
            battery_current_v1_charge_entity.inverter_charge_discharge_settings.cid: value
        }
        assert battery_current_v1_charge_entity.native_value == 50.0

    @pytest.mark.parametrize("value", [VARIANT1_VALUE, VARIANT2_VALUE])
    def test_native_value_discharge_current(self, battery_current_v1_discharge_entity, value):
        battery_current_v1_discharge_entity.coordinator.data = {
            battery_current_v1_discharge_entity.inverter_charge_discharge_settings.cid: value
        }
        assert battery_current_v1_discharge_entity.native_value == 0.0

    def test_native_value_no_data(self, battery_current_v1_charge_entity):
        battery_current_v1_charge_entity.coordinator.data = {
            battery_current_v1_charge_entity.inverter_charge_discharge_settings.cid: None
        }
        assert battery_current_v1_charge_entity.native_value is None

    def test_native_value_invalid_format(self, battery_current_v1_charge_entity):
        invalid_charge_current1 = (
            "invalid,0,09:00,10:00,11:00,12:00,0,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00"
        )
        battery_current_v1_charge_entity.coordinator.data = {
            battery_current_v1_charge_entity.inverter_charge_discharge_settings.cid: invalid_charge_current1
        }
        assert battery_current_v1_charge_entity.native_value is None

    async def test_async_set_native_value_variant1_charge_current(self, battery_current_v1_charge_entity):
        battery_current_v1_charge_entity.coordinator.data = {
            battery_current_v1_charge_entity.inverter_charge_discharge_settings.cid: self.VARIANT1_VALUE
        }
        await battery_current_v1_charge_entity.async_set_native_value(99.0)
        expected_value = "99,0,09:00,10:00,11:00,12:00,0,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00"
        battery_current_v1_charge_entity.coordinator.control.assert_awaited_once_with(
            battery_current_v1_charge_entity.inverter_charge_discharge_settings.cid, expected_value
        )

    async def test_async_set_native_value_variant1_discharge_current(self, battery_current_v1_discharge_entity):
        battery_current_v1_discharge_entity.coordinator.data = {
            battery_current_v1_discharge_entity.inverter_charge_discharge_settings.cid: self.VARIANT1_VALUE
        }
        await battery_current_v1_discharge_entity.async_set_native_value(99.0)
        expected_value = "50,99,09:00,10:00,11:00,12:00,0,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00"
        battery_current_v1_discharge_entity.coordinator.control.assert_awaited_once_with(
            battery_current_v1_discharge_entity.inverter_charge_discharge_settings.cid, expected_value
        )

    async def test_async_set_native_value_variant2_charge_current(self, battery_current_v1_charge_entity):
        battery_current_v1_charge_entity.coordinator.data = {
            battery_current_v1_charge_entity.inverter_charge_discharge_settings.cid: self.VARIANT2_VALUE
        }
        await battery_current_v1_charge_entity.async_set_native_value(99.0)
        expected_value = "99,0,09:00-10:00,11:00-12:00,0,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00"
        battery_current_v1_charge_entity.coordinator.control.assert_awaited_once_with(
            battery_current_v1_charge_entity.inverter_charge_discharge_settings.cid, expected_value
        )

    async def test_async_set_native_value_variant2_discharge_current(self, battery_current_v1_discharge_entity):
        battery_current_v1_discharge_entity.coordinator.data = {
            battery_current_v1_discharge_entity.inverter_charge_discharge_settings.cid: self.VARIANT2_VALUE
        }
        await battery_current_v1_discharge_entity.async_set_native_value(99.0)
        expected_value = "50,99,09:00-10:00,11:00-12:00,0,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00"
        battery_current_v1_discharge_entity.coordinator.control.assert_awaited_once_with(
            battery_current_v1_discharge_entity.inverter_charge_discharge_settings.cid, expected_value
        )

    async def test_async_set_native_value_no_current_settings(self, battery_current_v1_charge_entity):
        battery_current_v1_charge_entity.coordinator.data = {
            battery_current_v1_charge_entity.inverter_charge_discharge_settings.cid: None
        }
        await battery_current_v1_charge_entity.async_set_native_value(99.0)
        battery_current_v1_charge_entity.coordinator.control.assert_not_called()

    async def test_async_set_native_value_invalid_settings_format(self, battery_current_v1_charge_entity):
        invalid_format = "invalid format"
        battery_current_v1_charge_entity.coordinator.data = {
            battery_current_v1_charge_entity.inverter_charge_discharge_settings.cid: invalid_format
        }
        await battery_current_v1_charge_entity.async_set_native_value(99.0)
        battery_current_v1_charge_entity.coordinator.control.assert_not_called()


@pytest.fixture
def battery_current_v2_entity(mock_coordinator, any_inverter):
    return BatteryCurrentV2(
        coordinator=mock_coordinator,
        entity_description=NumberEntityDescription(key="any_key", name="any name"),
        inverter_charge_discharge_slot=any_inverter.charge_discharge_slots.charge_slot1,
        inverter_battery_max_charge_discharge_current=any_inverter.battery_max_charge_current,
    )


class TestBatteryCurrentV2:
    def test_attributes(self, battery_current_v2_entity):
        inverter_charge_discharge_slot = battery_current_v2_entity.inverter_charge_discharge_slot
        assert battery_current_v2_entity.native_min_value == inverter_charge_discharge_slot.current_min_value
        assert battery_current_v2_entity.native_max_value == inverter_charge_discharge_slot.current_max_value
        assert battery_current_v2_entity.native_step == inverter_charge_discharge_slot.current_step
        assert battery_current_v2_entity.native_unit_of_measurement == UnitOfElectricCurrent.AMPERE

    def test_native_max_value(self, battery_current_v2_entity):
        battery_current_v2_entity.coordinator.data = {
            battery_current_v2_entity.inverter_battery_max_charge_discharge_current.cid: "50"
        }
        assert battery_current_v2_entity.native_max_value == 50

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", 0.0),
            ("50", 50.0),
            ("100", 100.0),
            ("not a number", None),
            (None, None),
        ],
    )
    def test_native_value(self, battery_current_v2_entity, value, expected):
        battery_current_v2_entity.coordinator.data = {
            battery_current_v2_entity.inverter_charge_discharge_slot.current_cid: value
        }
        assert battery_current_v2_entity.native_value == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (50.4, "50"),
            (99.9, "100"),
        ],
    )
    async def test_set_native_value(self, battery_current_v2_entity, value, expected_str):
        await battery_current_v2_entity.async_set_native_value(value)
        battery_current_v2_entity.coordinator.control.assert_awaited_once_with(
            battery_current_v2_entity.inverter_charge_discharge_slot.current_cid, expected_str
        )


@pytest.fixture
def battery_soc_v2_entity(mock_coordinator, any_inverter):
    return BatterySocV2(
        coordinator=mock_coordinator,
        entity_description=NumberEntityDescription(key="any_key", name="any name"),
        inverter_charge_discharge_slot=any_inverter.charge_discharge_slots.charge_slot1,
        inverter_battery_over_discharge_soc=any_inverter.battery_over_discharge_soc,
        inverter_battery_max_charge_soc=any_inverter.battery_max_charge_soc,
    )


class TestBatterySocV2:
    def test_attributes(self, battery_soc_v2_entity):
        inverter_charge_discharge_slot = battery_soc_v2_entity.inverter_charge_discharge_slot
        assert battery_soc_v2_entity.native_min_value == inverter_charge_discharge_slot.soc_min_value
        assert battery_soc_v2_entity.native_max_value == inverter_charge_discharge_slot.soc_max_value
        assert battery_soc_v2_entity.native_step == inverter_charge_discharge_slot.soc_step
        assert battery_soc_v2_entity.native_unit_of_measurement == PERCENTAGE

    def test_native_min_value(self, battery_soc_v2_entity):
        battery_soc_v2_entity.coordinator.data = {battery_soc_v2_entity.inverter_battery_over_discharge_soc.cid: "10"}
        assert battery_soc_v2_entity.native_min_value == 11.0

    def test_native_max_value(self, battery_soc_v2_entity):
        battery_soc_v2_entity.coordinator.data = {battery_soc_v2_entity.inverter_battery_max_charge_soc.cid: "99"}
        assert battery_soc_v2_entity.native_max_value == 99

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", 0.0),
            ("50", 50.0),
            ("100", 100.0),
            ("not a number", None),
            (None, None),
        ],
    )
    def test_native_value(self, battery_soc_v2_entity, value, expected):
        battery_soc_v2_entity.coordinator.data = {battery_soc_v2_entity.inverter_charge_discharge_slot.soc_cid: value}
        assert battery_soc_v2_entity.native_value == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (50.4, "50"),
            (99.9, "100"),
        ],
    )
    async def test_set_native_value(self, battery_soc_v2_entity, value, expected_str):
        await battery_soc_v2_entity.async_set_native_value(value)
        battery_soc_v2_entity.coordinator.control.assert_awaited_once_with(
            battery_soc_v2_entity.inverter_charge_discharge_slot.soc_cid, expected_str
        )


@pytest.fixture
def max_output_power_entity(mock_coordinator, any_inverter):
    return MaxOutputPower(
        coordinator=mock_coordinator,
        entity_description=NumberEntityDescription(key="any_key", name="any name"),
        max_output_power=any_inverter.max_output_power,
    )


class TestMaxOutputPower:
    def test_attributes(self, max_output_power_entity):
        assert max_output_power_entity.native_min_value == 0
        assert max_output_power_entity.native_max_value == 100
        assert max_output_power_entity.native_step == 1
        assert max_output_power_entity.native_unit_of_measurement == PERCENTAGE

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", 0.0),
            ("50", 50.0),
            ("100", 100.0),
            ("not a number", None),
            (None, None),
        ],
    )
    def test_native_value(self, max_output_power_entity, value, expected):
        max_output_power_entity.coordinator.data = {max_output_power_entity.max_output_power.cid: value}
        assert max_output_power_entity.native_value == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (50.4, "50"),
            (99.9, "100"),
        ],
    )
    async def test_set_native_value(self, max_output_power_entity, value, expected_str):
        await max_output_power_entity.async_set_native_value(value)
        max_output_power_entity.coordinator.control.assert_awaited_once_with(
            max_output_power_entity.max_output_power.cid, expected_str
        )


@pytest.fixture
def max_export_power_entity(mock_coordinator, any_inverter):
    return MaxExportPower(
        coordinator=mock_coordinator,
        entity_description=NumberEntityDescription(key="any_key", name="any name"),
        max_export_power=any_inverter.max_export_power,
    )


@pytest.fixture
def max_export_power_entity_scaled_0_1(mock_coordinator, any_inverter):
    max_export_power = replace(any_inverter.max_export_power, scale=0.1)
    return MaxExportPower(
        coordinator=mock_coordinator,
        entity_description=NumberEntityDescription(key="any_key", name="any name"),
        max_export_power=max_export_power,
    )


class TestMaxExportPower:
    def test_attributes(self, max_export_power_entity):
        max_export_power = max_export_power_entity.max_export_power
        assert max_export_power_entity.native_min_value == max_export_power.min_value
        assert max_export_power_entity.native_max_value == max_export_power.max_value
        assert max_export_power_entity.native_step == max_export_power.step
        assert max_export_power_entity.native_unit_of_measurement == UnitOfPower.WATT

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", 0.0),
            ("50", 50.0),
            ("100", 100.0),
            ("not a number", None),
            (None, None),
        ],
    )
    def test_native_value(self, max_export_power_entity, value, expected):
        max_export_power_entity.coordinator.data = {max_export_power_entity.max_export_power.cid: value}
        assert max_export_power_entity.native_value == expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", 0.0),
            ("50", 500.0),
            ("100", 1000.0),
            ("not a number", None),
            (None, None),
        ],
    )
    def test_native_value_scaled_0_1(self, max_export_power_entity_scaled_0_1, value, expected):
        max_export_power_entity_scaled_0_1.coordinator.data = {
            max_export_power_entity_scaled_0_1.max_export_power.cid: value
        }
        assert max_export_power_entity_scaled_0_1.native_value == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (50.4, "50"),
            (99.9, "100"),
        ],
    )
    async def test_set_native_value(self, max_export_power_entity, value, expected_str):
        await max_export_power_entity.async_set_native_value(value)
        max_export_power_entity.coordinator.control.assert_awaited_once_with(
            max_export_power_entity.max_export_power.cid, expected_str
        )

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (1, "0"),
            (504, "50"),
            (999, "100"),
        ],
    )
    async def test_set_native_value_scaled_0_1(self, max_export_power_entity_scaled_0_1, value, expected_str):
        await max_export_power_entity_scaled_0_1.async_set_native_value(value)
        max_export_power_entity_scaled_0_1.coordinator.control.assert_awaited_once_with(
            max_export_power_entity_scaled_0_1.max_export_power.cid, expected_str
        )


@pytest.fixture
def power_limit_entity(mock_coordinator, any_inverter):
    return PowerLimit(
        coordinator=mock_coordinator,
        entity_description=NumberEntityDescription(key="any_key", name="any name"),
        power_limit=any_inverter.power_limit,
    )


class TestPowerLimit:
    def test_attributes(self, power_limit_entity):
        assert power_limit_entity.native_min_value == power_limit_entity.power_limit.min_value
        assert power_limit_entity.native_max_value == power_limit_entity.power_limit.max_value
        assert power_limit_entity.native_step == 1
        assert power_limit_entity.native_unit_of_measurement == PERCENTAGE

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", 0.0),
            ("50", 50.0),
            ("100", 100.0),
            ("not a number", None),
            (None, None),
        ],
    )
    def test_native_value(self, power_limit_entity, value, expected):
        power_limit_entity.coordinator.data = {power_limit_entity.power_limit.cid: value}
        assert power_limit_entity.native_value == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (50.4, "50"),
            (99.9, "100"),
        ],
    )
    async def test_set_native_value(self, power_limit_entity, value, expected_str):
        await power_limit_entity.async_set_native_value(value)
        power_limit_entity.coordinator.control.assert_awaited_once_with(
            power_limit_entity.power_limit.cid, expected_str
        )
