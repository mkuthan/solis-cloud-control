from dataclasses import replace

import pytest

from custom_components.solis_cloud_control.inverters.inverter import (
    Inverter,
)
from custom_components.solis_cloud_control.inverters.inverter_factory import (
    create_inverter,
    create_inverter_info,
)


@pytest.mark.asyncio
async def test_create_inverter_info(mock_api_client):
    mock_api_client.inverter_details.return_value = {
        "model": "any model",
        "version": "any version",
        "machine": "any machine",
        "energyStorageControl": "any energy storage control",
        "smartSupport": "any smart support",
        "generatorSupport": "any generator support",
        "power": 10,
        "powerStr": "kW",
    }

    inverter_sn = "any serial number"
    result = await create_inverter_info(mock_api_client, inverter_sn)

    assert result.serial_number == inverter_sn
    assert result.model == "any model"
    assert result.version == "any version"
    assert result.machine == "any machine"
    assert result.energy_storage_control == "any energy storage control"
    assert result.smart_support == "any smart support"
    assert result.generator_support == "any generator support"
    assert result.power == "10"
    assert result.power_unit == "kW"


@pytest.mark.asyncio
async def test_create_inverter_info_missing_fields(mock_api_client):
    mock_api_client.inverter_details.return_value = {}
    inverter_sn = "any serial number"

    result = await create_inverter_info(mock_api_client, inverter_sn)

    assert result.serial_number == inverter_sn
    assert result.model is None
    assert result.version is None
    assert result.machine is None
    assert result.energy_storage_control is None
    assert result.smart_support is None
    assert result.generator_support is None
    assert result.power is None
    assert result.power_unit is None


@pytest.mark.asyncio
async def test_create_inverter_unknown_hybrid_model(mock_api_client, any_inverter_info):
    inverter_info = replace(any_inverter_info, model="unknown model", energy_storage_control="1")
    result = await create_inverter(mock_api_client, inverter_info)

    assert result == Inverter.create_hybrid_inverter(inverter_info)


@pytest.mark.asyncio
async def test_create_inverter_unknown_string_model(mock_api_client, any_inverter_info):
    inverter_info = replace(any_inverter_info, model="unknown model", energy_storage_control="0")
    result = await create_inverter(mock_api_client, inverter_info)

    assert result == Inverter.create_string_inverter(inverter_info)


@pytest.mark.asyncio
async def test_create_inverter_specific_hybrid_model(mock_api_client, any_inverter_info):
    inverter_info = replace(any_inverter_info, model="3331")
    result = await create_inverter(mock_api_client, inverter_info)

    assert result != Inverter.create_string_inverter(inverter_info)


@pytest.mark.asyncio
async def test_create_inverter_specific_string_model(mock_api_client, any_inverter_info):
    inverter_info = replace(any_inverter_info, model="0200")
    result = await create_inverter(mock_api_client, inverter_info)

    assert result != Inverter.create_hybrid_inverter(inverter_info)
