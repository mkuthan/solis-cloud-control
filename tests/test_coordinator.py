from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solis_cloud_control.api import SolisCloudControlApiError
from custom_components.solis_cloud_control.const import (
    CID_CHECK_CHARGE_DISCHARGE_MODE,
    DOMAIN,
)
from custom_components.solis_cloud_control.coordinator import (
    _CHARGE_DISCHARGE_SLOTS_CIDS_LIST,
    _DEFAULT_CIDS_LIST,
    _NEW_CHARGE_DISCHARGE_MODE,
    SolisCloudControlCoordinator,
)


@pytest.fixture
def config_entry(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_api_client():
    return AsyncMock()


@pytest.fixture
def any_inverter_sn():
    return "any_inverter_sn"


@pytest.fixture
def coordinator(hass: HomeAssistant, config_entry, mock_api_client, any_inverter_sn):
    return SolisCloudControlCoordinator(
        hass=hass,
        config_entry=config_entry,
        api_client=mock_api_client,
        inverter_sn=any_inverter_sn,
    )


async def test_async_update_data_old_mode(hass: HomeAssistant, coordinator, mock_api_client, any_inverter_sn):
    mock_api_client.read.return_value = "0"  # old mode
    any_data = {cid: f"value_{cid}" for cid in _DEFAULT_CIDS_LIST}
    mock_api_client.read_batch.return_value = any_data

    data = await coordinator._async_update_data()

    mock_api_client.read.assert_called_once_with(any_inverter_sn, CID_CHECK_CHARGE_DISCHARGE_MODE)
    mock_api_client.read_batch.assert_called_once_with(
        any_inverter_sn,
        _DEFAULT_CIDS_LIST,
        retry_count=5,
        retry_delay=10,
    )

    assert data == {cid: any_data.get(cid) for cid in _DEFAULT_CIDS_LIST}


async def test_async_update_data_new_mode(hass: HomeAssistant, coordinator, mock_api_client, any_inverter_sn):
    mock_api_client.read.return_value = str(_NEW_CHARGE_DISCHARGE_MODE)
    all_cids = _DEFAULT_CIDS_LIST + _CHARGE_DISCHARGE_SLOTS_CIDS_LIST
    any_data = {cid: f"value_{cid}" for cid in all_cids}
    mock_api_client.read_batch.return_value = any_data

    data = await coordinator._async_update_data()

    mock_api_client.read.assert_called_once_with(any_inverter_sn, CID_CHECK_CHARGE_DISCHARGE_MODE)
    mock_api_client.read_batch.assert_called_once_with(
        any_inverter_sn,
        all_cids,
        retry_count=5,
        retry_delay=10,
    )

    assert data == {cid: any_data.get(cid) for cid in all_cids}


async def test_async_update_data_api_error(hass: HomeAssistant, coordinator, mock_api_client, any_inverter_sn):
    any_error = "any error"
    mock_api_client.read.side_effect = SolisCloudControlApiError(any_error)

    with pytest.raises(UpdateFailed) as exc_info:
        await coordinator._async_update_data()

    assert str(exc_info.value) == any_error

    mock_api_client.read.assert_called_once_with(any_inverter_sn, CID_CHECK_CHARGE_DISCHARGE_MODE)
    mock_api_client.read_batch.assert_not_called()


async def test_control_success(hass: HomeAssistant, coordinator, mock_api_client, any_inverter_sn):
    any_cid = 123
    any_value = "any_value"

    mock_api_client.control.return_value = None
    mock_api_client.read.return_value = any_value

    with patch.object(coordinator, "async_request_refresh", AsyncMock()) as mock_refresh:
        await coordinator.control(any_cid, any_value)

        mock_api_client.control.assert_called_once_with(any_inverter_sn, any_cid, any_value, None)
        mock_api_client.read.assert_called_once_with(any_inverter_sn, any_cid)
        mock_refresh.assert_called_once()


async def test_control_retry_and_fail(hass: HomeAssistant, coordinator, mock_api_client, any_inverter_sn):
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


async def test_control_api_error(hass: HomeAssistant, coordinator, mock_api_client, any_inverter_sn):
    any_cid = 123
    any_value = "any_value"
    any_error = "any error"

    mock_api_client.control.side_effect = SolisCloudControlApiError(any_error)

    with pytest.raises(SolisCloudControlApiError) as exc_info:
        await coordinator.control(any_cid, any_value)

    assert str(exc_info.value) == any_error

    mock_api_client.control.assert_called_once_with(any_inverter_sn, any_cid, any_value, None)
