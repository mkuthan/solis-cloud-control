from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiError
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
    read_batch_cids = any_inverter.read_batch_cids
    read_cids = any_inverter.read_cids

    read_batch_data = {cid: f"value_{cid}" for cid in read_batch_cids}
    mock_api_client.read_batch.return_value = read_batch_data

    for read_cid in read_cids:
        mock_api_client.read.side_effect = lambda serial_number, read_cid, **kwargs: f"value_{read_cid}"  # noqa: ARG005

    data = await coordinator._async_update_data()

    mock_api_client.read_batch.assert_called_once_with(
        any_inverter.info.serial_number,
        read_batch_cids,
        max_retry_time=180,
    )

    for read_cid in read_cids:
        mock_api_client.read.assert_called_once_with(
            any_inverter.info.serial_number,
            read_cid,
            max_retry_time=60,
        )

    assert data == {cid: f"value_{cid}" for cid in any_inverter.all_cids}


async def test_async_update_data_api_error(hass: HomeAssistant, coordinator, mock_api_client):
    any_error = "any error"
    mock_api_client.read_batch.side_effect = SolisCloudControlApiError(any_error)

    with pytest.raises(UpdateFailed) as exc_info:
        await coordinator._async_update_data()

    assert str(exc_info.value) == any_error

    mock_api_client.read_batch.assert_called_once_with(
        coordinator._inverter.info.serial_number,
        coordinator._inverter.read_batch_cids,
        max_retry_time=180,
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


async def test_control_success_with_data(hass: HomeAssistant, coordinator, mock_api_client, any_inverter):
    any_cid = 123
    any_value = "any_value"
    initial_value = "initial_value"

    coordinator.data = {any_cid: initial_value}

    mock_api_client.control.return_value = None
    mock_api_client.read.return_value = any_value

    with (
        patch.object(coordinator, "async_request_refresh", AsyncMock()) as mock_refresh,
        patch.object(coordinator, "async_set_updated_data") as mock_set_updated_data,
    ):
        await coordinator.control(any_cid, any_value)

        mock_api_client.control.assert_called_once_with(any_inverter.info.serial_number, any_cid, any_value, None)
        mock_api_client.read.assert_called_once_with(any_inverter.info.serial_number, any_cid)

        mock_refresh.assert_not_called()
        mock_set_updated_data.assert_called_once_with({any_cid: any_value})


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
        await coordinator.control(any_cid, any_value, retry_delay=0)

    assert f"Failed to set value for CID {any_cid}" in str(exc_info.value)
    assert mock_api_client.control.call_count == 2  # Initial + 1 retry
    assert mock_api_client.read.call_count == 2  # Initial + 1 retry
    mock_refresh.assert_not_called()


async def test_control_no_check_success(hass: HomeAssistant, coordinator, mock_api_client, any_inverter):
    any_cid = 123
    any_value = "any_value"
    any_old_value = "any_old_value"

    mock_api_client.control.return_value = None

    with patch.object(coordinator, "async_request_refresh", AsyncMock()) as mock_refresh:
        await coordinator.control_no_check(any_cid, any_value, any_old_value)

        mock_api_client.control.assert_called_once_with(
            any_inverter.info.serial_number, any_cid, any_value, any_old_value
        )
        mock_api_client.read.assert_not_called()
        mock_refresh.assert_called_once()


async def test_control_no_check_success_with_data(hass: HomeAssistant, coordinator, mock_api_client, any_inverter):
    any_cid = 123
    any_value = "any_value"
    initial_value = "initial_value"

    coordinator.data = {any_cid: initial_value}

    mock_api_client.control.return_value = None

    with (
        patch.object(coordinator, "async_request_refresh", AsyncMock()) as mock_refresh,
        patch.object(coordinator, "async_set_updated_data") as mock_set_updated_data,
    ):
        await coordinator.control_no_check(any_cid, any_value)

        mock_api_client.control.assert_called_once_with(any_inverter.info.serial_number, any_cid, any_value, None)

        mock_refresh.assert_not_called()
        mock_set_updated_data.assert_called_once_with({any_cid: any_value})


async def test_control_no_check_api_error(hass: HomeAssistant, coordinator, mock_api_client):
    any_cid = 123
    any_value = "any_value"
    any_error = "any error"

    mock_api_client.control.side_effect = SolisCloudControlApiError(any_error)

    with pytest.raises(SolisCloudControlApiError) as exc_info:
        await coordinator.control_no_check(any_cid, any_value)

    assert str(exc_info.value) == any_error

    mock_api_client.control.assert_called_once_with(coordinator._inverter.info.serial_number, any_cid, any_value, None)
    mock_api_client.read.assert_not_called()
