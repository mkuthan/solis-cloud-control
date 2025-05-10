import pytest

from custom_components.solis_cloud_control.inverter import (
    Inverter,
)
from custom_components.solis_cloud_control.inverter_factory import (
    _CHARGE_DISCHARGE_MODE_USING_SLOTS,
    create_inverter,
    create_inverter_info,
)


@pytest.mark.asyncio
async def test_create_inverter_info(mock_api_client):
    mock_api_client.inverter_details.return_value = {
        "model": "any model",
        "version": "any version",
        "machine": "any machine",
    }

    inverter_sn = "any serial number"
    result = await create_inverter_info(mock_api_client, inverter_sn)

    assert result.serial_number == inverter_sn
    assert result.model == "any model"
    assert result.version == "any version"
    assert result.machine == "any machine"


@pytest.mark.asyncio
async def test_create_inverter_info_missing_fields(mock_api_client):
    mock_api_client.inverter_details.return_value = {}
    inverter_sn = "any serial number"

    result = await create_inverter_info(mock_api_client, inverter_sn)

    assert result.serial_number == inverter_sn
    assert result.model == "Unknown"
    assert result.version == "Unknown"
    assert result.machine == "Unknown"


@pytest.mark.asyncio
async def test_create_inverter_unknown_model(mock_api_client, any_inverter_info):
    any_inverter_info.model = "unknown model"
    result = await create_inverter(mock_api_client, any_inverter_info)

    assert result == Inverter(info=any_inverter_info)


@pytest.mark.asyncio
async def test_create_inverter_3331_model_with_slots(mock_api_client, any_inverter_info):
    any_inverter_info.model = "3331"
    mock_api_client.read.return_value = str(_CHARGE_DISCHARGE_MODE_USING_SLOTS)

    result = await create_inverter(mock_api_client, any_inverter_info)

    assert result is not Inverter(info=any_inverter_info)
    assert result.charge_discharge_slots is not None
    assert result.charge_discharge_settings is None


@pytest.mark.asyncio
async def test_create_inverter_3331_model_with_settings(mock_api_client, any_inverter_info):
    any_inverter_info.model = "3331"
    mock_api_client.read.return_value = "unknown mode"

    result = await create_inverter(mock_api_client, any_inverter_info)

    assert result is not Inverter(info=any_inverter_info)
    assert result.charge_discharge_slots is None
    assert result.charge_discharge_settings is not None
