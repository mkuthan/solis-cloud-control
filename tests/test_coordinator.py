from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.solis_cloud_control.coordinator import SolisCloudControlCoordinator, SolisCloudControlData
from custom_components.solis_cloud_control.services.cid_service import CidServiceError

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.fixture
def mock_cid_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def coordinator(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_cid_service: AsyncMock,
) -> SolisCloudControlCoordinator:
    return SolisCloudControlCoordinator(
        hass=hass,
        config_entry=mock_config_entry,
        cid_service=mock_cid_service,
    )


async def test_async_update_data(
    hass: HomeAssistant, coordinator: SolisCloudControlCoordinator, mock_cid_service: AsyncMock
) -> None:
    mock_cid_service.read_all.return_value = {1: "value_1", 2: None}

    data = await coordinator._async_update_data()

    mock_cid_service.read_all.assert_awaited_once_with()
    assert isinstance(data, SolisCloudControlData)
    assert data == SolisCloudControlData(cids={1: "value_1", 2: None})
    assert data.remote_dispatch is None


async def test_async_update_data_cid_service_error(
    hass: HomeAssistant, coordinator: SolisCloudControlCoordinator, mock_cid_service: AsyncMock
) -> None:
    any_error = "any error"
    mock_cid_service.read_all.side_effect = CidServiceError(any_error)

    with pytest.raises(UpdateFailed) as exc_info:
        await coordinator._async_update_data()

    assert str(exc_info.value) == any_error
    mock_cid_service.read_all.assert_awaited_once_with()


async def test_control_success(
    hass: HomeAssistant, coordinator: SolisCloudControlCoordinator, mock_cid_service: AsyncMock
) -> None:
    any_cid = 123
    any_value = "any_value"
    any_old_value = "any_old_value"
    any_initial_value = "initial_value"

    coordinator.data = SolisCloudControlData(cids={any_cid: any_initial_value})

    with (
        patch.object(coordinator, "async_request_refresh", AsyncMock()) as mock_request_refresh,
        patch.object(coordinator, "async_set_updated_data", Mock()) as mock_set_updated_data,
    ):
        await coordinator.control(any_cid, any_value, any_old_value)

        mock_set_updated_data.assert_called_once_with(SolisCloudControlData(cids={any_cid: any_value}))
        mock_cid_service.control.assert_awaited_once_with(any_cid, any_value, any_old_value)
        mock_request_refresh.assert_called_once()


async def test_control_success_without_data(
    hass: HomeAssistant, coordinator: SolisCloudControlCoordinator, mock_cid_service: AsyncMock
) -> None:
    any_cid = 123
    any_value = "any_value"
    any_old_value = "any_old_value"

    with (
        patch.object(coordinator, "async_request_refresh", AsyncMock()) as mock_request_refresh,
        patch.object(coordinator, "async_set_updated_data", Mock()) as mock_set_updated_data,
    ):
        await coordinator.control(any_cid, any_value, any_old_value)

        mock_set_updated_data.assert_not_called()
        mock_cid_service.control.assert_awaited_once_with(any_cid, any_value, any_old_value)
        mock_request_refresh.assert_called_once()


async def test_control_cid_service_error(
    hass: HomeAssistant, coordinator: SolisCloudControlCoordinator, mock_cid_service: AsyncMock
) -> None:
    any_cid = 123
    any_value = "any_value"
    any_old_value = "any_old_value"
    any_initial_value = "initial_value"
    any_error = "any error"

    coordinator.data = SolisCloudControlData(cids={any_cid: any_initial_value})

    mock_cid_service.control.side_effect = CidServiceError(any_error)

    with (
        patch.object(coordinator, "async_request_refresh", AsyncMock()) as mock_request_refresh,
        patch.object(coordinator, "async_set_updated_data", Mock()) as mock_set_updated_data,
    ):
        with pytest.raises(CidServiceError) as exc_info:
            await coordinator.control(any_cid, any_value, any_old_value)

        assert str(exc_info.value) == any_error

        mock_set_updated_data.assert_called_once_with(SolisCloudControlData(cids={any_cid: any_value}))
        mock_cid_service.control.assert_awaited_once_with(any_cid, any_value, any_old_value)
        mock_request_refresh.assert_called_once()
