import pytest


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
    any_inverter_info.power = power
    any_inverter_info.power_unit = power_unit

    assert any_inverter_info.power_watts == expected_power
