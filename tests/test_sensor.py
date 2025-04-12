import pytest
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.const import PERCENTAGE

from custom_components.solis_cloud_control.const import (
    CID_BATTERY_FORCE_CHARGE_SOC,
)
from custom_components.solis_cloud_control.sensor import BatterySocSensor


@pytest.fixture
def battery_soc_sensor(mock_coordinator):
    return BatterySocSensor(
        coordinator=mock_coordinator,
        entity_description=SensorEntityDescription(
            key="test_battery_soc",
            name="Test Battery SOC",
        ),
        cid=CID_BATTERY_FORCE_CHARGE_SOC,
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
            (None, None),
        ],
    )
    def test_native_value(self, battery_soc_sensor, value, expected):
        battery_soc_sensor.coordinator.data = {CID_BATTERY_FORCE_CHARGE_SOC: value}
        assert battery_soc_sensor.native_value == expected
