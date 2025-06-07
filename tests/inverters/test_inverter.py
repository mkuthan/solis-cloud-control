from dataclasses import replace

import pytest

from custom_components.solis_cloud_control.inverters.inverter import InverterOnOff


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "power, power_unit, expected_power",
    [
        ("5", "kW", 5000.0),
        ("5000", "W", 5000.0),
        ("5.5", "kW", 5500.0),
        ("5500.5", "W", 5500.5),
        ("invalid", "kW", None),
        ("5", "invalid", None),
        ("5", None, None),
        (None, "kW", None),
    ],
)
async def test_inverter_info_power_watts(mock_api_client, any_inverter_info, power, power_unit, expected_power):
    inverter = replace(any_inverter_info, power=power, power_unit=power_unit)

    assert inverter.power_watts == expected_power


@pytest.mark.parametrize(
    "energy_storage_control,expected",
    [
        ("0", True),
        ("1", False),
        (None, False),
        ("", False),
        ("unexpected", False),
    ],
)
def test_inverter_info_is_string_inverter(any_inverter_info, energy_storage_control, expected):
    inverter = replace(any_inverter_info, energy_storage_control=energy_storage_control)
    assert inverter.is_string_inverter == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("190", True),
        ("222", True),
        ("0", False),
        ("", False),
        ("invalid", False),
        (None, False),
    ],
)
def test_inverter_on_off_is_valid_value(value, expected):
    inverter_on_off = InverterOnOff()
    assert inverter_on_off.is_valid_value(value) == expected
