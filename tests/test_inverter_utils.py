from unittest.mock import AsyncMock

import pytest

from custom_components.solis_cloud_control.api import SolisCloudControlApiClient
from custom_components.solis_cloud_control.inverter_utils import (
    _CHARGE_DISCHARGE_MODE_SLOTS_ENABLED,
    charge_discharge_mode_slots_enabled,
)


@pytest.fixture
def mock_api_client():
    client = AsyncMock(spec=SolisCloudControlApiClient)
    return client


@pytest.mark.asyncio
async def test_charge_discharge_mode_slots_enabled_returns_true_when_mode_matches(mock_api_client):
    mock_api_client.read.return_value = str(_CHARGE_DISCHARGE_MODE_SLOTS_ENABLED)
    inverter_sn = "any inverter sn"

    result = await charge_discharge_mode_slots_enabled(mock_api_client, inverter_sn)

    assert result is True


@pytest.mark.asyncio
async def test_charge_discharge_mode_slots_enabled_returns_false_when_mode_does_not_match(mock_api_client):
    mock_api_client.read.return_value = "some_other_value"
    inverter_sn = "any inverter sn"

    result = await charge_discharge_mode_slots_enabled(mock_api_client, inverter_sn)

    assert result is False


@pytest.mark.asyncio
async def test_charge_discharge_mode_slots_enabled_returns_false_when_api_returns_none(mock_api_client):
    mock_api_client.read.return_value = None
    inverter_sn = "any inverter sn"

    result = await charge_discharge_mode_slots_enabled(mock_api_client, inverter_sn)

    assert result is False
