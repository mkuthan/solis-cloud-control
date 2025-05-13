from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.solis_cloud_control.api import SolisCloudControlApiError
from custom_components.solis_cloud_control.coordinator import SolisCloudControlCoordinator


@pytest.fixture
def coordinator(hass: HomeAssistant, mock_config_entry, mock_api_client, any_inverter):
    return SolisCloudControlCoordinator(
        hass=hass,
        config_entry=mock_config_entry,
        api_client=mock_api_client,
        inverter=any_inverter,
    )


async def test_async_update_data(hass: HomeAssistant, coordinator, mock_api_client, any_inverter):
    all_cids = any_inverter.all_cids

    any_data = {cid: f"value_{cid}" for cid in all_cids}
    mock_api_client.read_batch.return_value = any_data

    data = await coordinator._async_update_data()

    mock_api_client.read_batch.assert_called_once_with(
        any_inverter.info.serial_number,
        all_cids,
        retry_count=5,
        retry_delay=10,
    )

    assert data == {cid: any_data.get(cid) for cid in all_cids}


async def test_async_update_data_api_error(hass: HomeAssistant, coordinator, mock_api_client):
    any_error = "any error"
    mock_api_client.read_batch.side_effect = SolisCloudControlApiError(any_error)

    with pytest.raises(UpdateFailed) as exc_info:
        await coordinator._async_update_data()

    assert str(exc_info.value) == any_error

    mock_api_client.read_batch.assert_called_once_with(
        coordinator._inverter.info.serial_number,
        coordinator._inverter.all_cids,
        retry_count=5,
        retry_delay=10,
    )


async def test_control_success(hass: HomeAssistant, coordinator, mock_api_client, any_inverter):
    any_cid = 123
    any_value = "any_value"

    mock_api_client.control.return_value = None
    mock_api_client.read.return_value = any_value

    with patch.object(coordinator, "async_request_refresh", AsyncMock()) as mock_refresh:
        await coordinator.control(any_cid, any_value)

        mock_api_client.control.assert_called_once_with(any_inverter.info.serial_number, any_cid, any_value, None)
        mock_api_client.read.assert_called_once_with(any_inverter.info.serial_number, any_cid)
        mock_refresh.assert_called_once()


async def test_control_api_error(hass: HomeAssistant, coordinator, mock_api_client, any_inverter):
    any_cid = 123
    any_value = "any_value"
    any_error = "any error"

    mock_api_client.control.side_effect = SolisCloudControlApiError(any_error)

    with pytest.raises(SolisCloudControlApiError) as exc_info:
        await coordinator.control(any_cid, any_value)

    assert str(exc_info.value) == any_error

    mock_api_client.control.assert_called_once_with(any_inverter.info.serial_number, any_cid, any_value, None)


async def test_control_retry_and_fail(hass: HomeAssistant, coordinator, mock_api_client):
    any_cid = 123
    any_value = "any_value"
    different_value = "different_value"

    mock_api_client.control.return_value = None
    mock_api_client.read.return_value = different_value

    with (
        pytest.raises(HomeAssistantError) as exc_info,
        patch.object(coordinator, "async_request_refresh", AsyncMock()) as mock_refresh,
    ):
        await coordinator.control(any_cid, any_value)

    assert f"Failed to set value for CID {any_cid}" in str(exc_info.value)
    assert mock_api_client.control.call_count == 2  # Initial + 1 retry
    assert mock_api_client.read.call_count == 2  # Initial + 1 retry
    mock_refresh.assert_not_called()
