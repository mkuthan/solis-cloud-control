from unittest.mock import patch

import pytest

from custom_components.solis_cloud_control.inverter import (
    Inverter,
)
from custom_components.solis_cloud_control.inverter_factory import (
    create_inverter,
    create_inverter_info,
)


@pytest.mark.asyncio
async def test_create_inverter_info(mock_api_client):
    mock_api_client.inverter_details.return_value = {
        "model": "any model",
        "version": "any version",
        "machine": "any machine",
        "power": 10,
        "powerStr": "kW",
    }

    inverter_sn = "any serial number"
    result = await create_inverter_info(mock_api_client, inverter_sn)

    assert result.serial_number == inverter_sn
    assert result.model == "any model"
    assert result.version == "any version"
    assert result.machine == "any machine"
    assert result.power == 10_000


@pytest.mark.asyncio
async def test_create_inverter_info_missing_fields(mock_api_client):
    mock_api_client.inverter_details.return_value = {}
    inverter_sn = "any serial number"

    result = await create_inverter_info(mock_api_client, inverter_sn)

    assert result.serial_number == inverter_sn
    assert result.model == "Unknown"
    assert result.version == "Unknown"
    assert result.machine == "Unknown"
    assert result.power is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "power_details, expected_power",
    [
        ({"power": "5", "powerStr": "kW"}, 5000.0),
        ({"power": "5000", "powerStr": "W"}, 5000.0),
        ({"power": "5.5", "powerStr": "kW"}, 5500.0),
        ({"power": "5500.5", "powerStr": "W"}, 5500.5),
        ({"power": "invalid", "powerStr": "kW"}, None),
        ({"power": "5", "powerStr": "invalid"}, None),
        ({"power": "5"}, None),
        ({"powerStr": "kW"}, None),
    ],
)
async def test_create_inverter_info_power(mock_api_client, power_details, expected_power):
    mock_api_client.inverter_details.return_value = power_details

    inverter_sn = "any serial number"
    result = await create_inverter_info(mock_api_client, inverter_sn)

    assert result.power == expected_power


@pytest.mark.asyncio
async def test_create_inverter_unknown_model(mock_api_client, any_inverter_info):
    any_inverter_info.model = "unknown model"
    result = await create_inverter(mock_api_client, any_inverter_info)

    assert result == Inverter(info=any_inverter_info)


@pytest.mark.asyncio
@patch("custom_components.solis_cloud_control.inverter_factory.charge_discharge_mode_slots_enabled")
async def test_create_inverter_3331_model_with_charge_discharge_slots(
    mock_charge_discharge_mode_slots_enabled, mock_api_client, any_inverter_info
):
    any_inverter_info.model = "3331"
    mock_charge_discharge_mode_slots_enabled.return_value = True

    result = await create_inverter(mock_api_client, any_inverter_info)

    assert result is not Inverter(info=any_inverter_info)
    assert result.charge_discharge_slots is not None
    assert result.charge_discharge_settings is None


@pytest.mark.asyncio
@patch("custom_components.solis_cloud_control.inverter_factory.charge_discharge_mode_slots_enabled")
async def test_create_inverter_3331_model_with_charge_discharge_settings(
    mock_charge_discharge_mode_slots_enabled, mock_api_client, any_inverter_info
):
    any_inverter_info.model = "3331"
    mock_charge_discharge_mode_slots_enabled.return_value = False

    result = await create_inverter(mock_api_client, any_inverter_info)

    assert result is not Inverter(info=any_inverter_info)
    assert result.charge_discharge_slots is None
    assert result.charge_discharge_settings is not None
