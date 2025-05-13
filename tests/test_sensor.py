import pytest
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.const import PERCENTAGE, UnitOfElectricCurrent

from custom_components.solis_cloud_control.sensor import (
    BatteryCurrentSensor,
    BatterySocSensor,
)


@pytest.fixture
def battery_soc_sensor(mock_coordinator, any_inverter):
    return BatterySocSensor(
        coordinator=mock_coordinator,
        entity_description=SensorEntityDescription(
            key="test_battery_soc",
            name="Test Battery SOC",
        ),
        battery_soc=any_inverter.battery_force_charge_soc,
    )


@pytest.fixture
def battery_current_sensor(mock_coordinator, any_inverter):
    return BatteryCurrentSensor(
        coordinator=mock_coordinator,
        entity_description=SensorEntityDescription(
            key="test_battery_current",
            name="Test Battery Current",
        ),
        battery_current=any_inverter.battery_max_charge_current,
    )


class TestBatterySocSensor:
    def test_attributes(self, battery_soc_sensor):
        assert battery_soc_sensor.native_unit_of_measurement == PERCENTAGE

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
    def test_native_value(self, battery_soc_sensor, value, expected):
        battery_soc_sensor.coordinator.data = {battery_soc_sensor.battery_soc.cid: value}
        assert battery_soc_sensor.native_value == expected


class TestBatteryCurrentSensor:
    def test_attributes(self, battery_current_sensor):
        assert battery_current_sensor.native_unit_of_measurement == UnitOfElectricCurrent.AMPERE

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", 0.0),
            ("10.5", 10.5),
            ("100", 100.0),
            ("not a number", None),
            (None, None),
        ],
    )
    def test_native_value(self, battery_current_sensor, value, expected):
        battery_current_sensor.coordinator.data = {battery_current_sensor.battery_current.cid: value}
        assert battery_current_sensor.native_value == expected
