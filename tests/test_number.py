from dataclasses import replace

import pytest
from homeassistant.components.number import NumberEntityDescription
from homeassistant.const import PERCENTAGE, UnitOfElectricCurrent, UnitOfPower

from custom_components.solis_cloud_control.number import (
    BatteryCurrentV2,
    BatterySocV2,
    MaxExportPower,
    MaxOutputPower,
    PowerLimit,
)


@pytest.fixture
def battery_current_entity(mock_coordinator, any_inverter):
    return BatteryCurrentV2(
        coordinator=mock_coordinator,
        entity_description=NumberEntityDescription(
            key="any_key",
            name="any name",
        ),
        charge_discharge_slot=any_inverter.charge_discharge_slots.charge_slot1,
        battery_max_charge_discharge_current=any_inverter.battery_max_charge_current,
    )


class TestBatteryCurrent:
    def test_attributes(self, battery_current_entity):
        charge_discharge_slot = battery_current_entity.charge_discharge_slot
        assert battery_current_entity.native_min_value == charge_discharge_slot.current_min_value
        assert battery_current_entity.native_max_value == charge_discharge_slot.current_max_value
        assert battery_current_entity.native_step == charge_discharge_slot.current_step
        assert battery_current_entity.native_unit_of_measurement == UnitOfElectricCurrent.AMPERE

    def test_native_max_value(self, battery_current_entity):
        battery_current_entity.coordinator.data = {
            battery_current_entity.battery_max_charge_discharge_current.cid: "50"
        }
        assert battery_current_entity.native_max_value == 50

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
    def test_native_value(self, battery_current_entity, value, expected):
        battery_current_entity.coordinator.data = {battery_current_entity.charge_discharge_slot.current_cid: value}
        assert battery_current_entity.native_value == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (50.4, "50"),
            (99.9, "100"),
        ],
    )
    async def test_set_native_value(self, battery_current_entity, value, expected_str):
        await battery_current_entity.async_set_native_value(value)
        battery_current_entity.coordinator.control.assert_awaited_once_with(
            battery_current_entity.charge_discharge_slot.current_cid, expected_str
        )


@pytest.fixture
def battery_soc_entity(mock_coordinator, any_inverter):
    return BatterySocV2(
        coordinator=mock_coordinator,
        entity_description=NumberEntityDescription(
            key="any_key",
            name="any name",
        ),
        charge_discharge_slot=any_inverter.charge_discharge_slots.charge_slot1,
        battery_over_discharge_soc=any_inverter.battery_over_discharge_soc,
        battery_max_charge_soc=any_inverter.battery_max_charge_soc,
    )


class TestBatterySoc:
    def test_attributes(self, battery_soc_entity):
        charge_discharge_slot = battery_soc_entity.charge_discharge_slot
        assert battery_soc_entity.native_min_value == charge_discharge_slot.soc_min_value
        assert battery_soc_entity.native_max_value == charge_discharge_slot.soc_max_value
        assert battery_soc_entity.native_step == charge_discharge_slot.soc_step
        assert battery_soc_entity.native_unit_of_measurement == PERCENTAGE

    def test_native_min_value(self, battery_soc_entity):
        battery_soc_entity.coordinator.data = {battery_soc_entity.battery_over_discharge_soc.cid: "10"}
        assert battery_soc_entity.native_min_value == 11.0

    def test_native_max_value(self, battery_soc_entity):
        battery_soc_entity.coordinator.data = {battery_soc_entity.battery_max_charge_soc.cid: "99"}
        assert battery_soc_entity.native_max_value == 99

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
    def test_native_value(self, battery_soc_entity, value, expected):
        battery_soc_entity.coordinator.data = {battery_soc_entity.charge_discharge_slot.soc_cid: value}
        assert battery_soc_entity.native_value == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (50.4, "50"),
            (99.9, "100"),
        ],
    )
    async def test_set_native_value(self, battery_soc_entity, value, expected_str):
        await battery_soc_entity.async_set_native_value(value)
        battery_soc_entity.coordinator.control.assert_awaited_once_with(
            battery_soc_entity.charge_discharge_slot.soc_cid, expected_str
        )


@pytest.fixture
def max_output_power_entity(mock_coordinator, any_inverter):
    return MaxOutputPower(
        coordinator=mock_coordinator,
        entity_description=NumberEntityDescription(
            key="any_key",
            name="any name",
        ),
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
        entity_description=NumberEntityDescription(
            key="any_key",
            name="any name",
        ),
        max_export_power=any_inverter.max_export_power,
    )


@pytest.fixture
def max_export_power_entity_scaled_0_1(mock_coordinator, any_inverter):
    max_export_power = replace(any_inverter.max_export_power, scale=0.1)
    return MaxExportPower(
        coordinator=mock_coordinator,
        entity_description=NumberEntityDescription(
            key="any_key",
            name="any name",
        ),
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
        entity_description=NumberEntityDescription(
            key="any_key",
            name="any name",
        ),
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
