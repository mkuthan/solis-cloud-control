from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.solis_cloud_control.coordinator import SolisCloudControlCoordinator, SolisCloudControlData
from custom_components.solis_cloud_control.domain.remote_dispatch import (
    HOLDING_COUNT,
    HOLDING_START,
    DispatchCapabilities,
    RemoteDispatch,
)
from custom_components.solis_cloud_control.services.cid_service import CidServiceError
from custom_components.solis_cloud_control.services.register_service import RegisterServiceError

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.fixture
def mock_cid_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_register_service() -> AsyncMock:
    service = AsyncMock()
    service.read_all.return_value = {}
    return service


@pytest.fixture
def dispatch_capabilities() -> DispatchCapabilities:
    return DispatchCapabilities(supported=True, version=3)


@pytest.fixture
def coordinator(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_cid_service: AsyncMock,
    mock_register_service: AsyncMock,
    dispatch_capabilities: DispatchCapabilities,
) -> SolisCloudControlCoordinator:
    return SolisCloudControlCoordinator(
        hass=hass,
        config_entry=mock_config_entry,
        cid_service=mock_cid_service,
        register_service=mock_register_service,
        dispatch_capabilities=dispatch_capabilities,
    )


async def test_async_update_data(
    hass: HomeAssistant,
    coordinator: SolisCloudControlCoordinator,
    mock_cid_service: AsyncMock,
    mock_register_service: AsyncMock,
) -> None:
    mock_cid_service.read_all.return_value = {1: "value_1", 2: None}
    mock_register_service.read_all.return_value = {44100: 1}

    data = await coordinator._async_update_data()

    mock_cid_service.read_all.assert_awaited_once_with()
    mock_register_service.read_all.assert_awaited_once_with()
    assert isinstance(data, SolisCloudControlData)
    assert data == SolisCloudControlData(cids={1: "value_1", 2: None})
    assert data.remote_dispatch is None
    assert coordinator._registers == {44100: 1}


async def test_async_update_data_decodes_remote_dispatch(
    coordinator: SolisCloudControlCoordinator,
    mock_register_service: AsyncMock,
) -> None:
    registers = {HOLDING_START + offset: 0 for offset in range(HOLDING_COUNT)}
    registers[HOLDING_START + 1] = 15
    mock_register_service.read_all.return_value = registers

    data = await coordinator._async_update_data()

    assert coordinator._registers == registers
    assert data.remote_dispatch is not None
    assert data.remote_dispatch.settings is not None
    assert data.remote_dispatch.settings.failsafe_minutes == 15


async def test_async_update_data_unknown_dispatch_version(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_cid_service: AsyncMock,
    mock_register_service: AsyncMock,
) -> None:
    coordinator = SolisCloudControlCoordinator(
        hass=hass,
        config_entry=mock_config_entry,
        cid_service=mock_cid_service,
        register_service=mock_register_service,
        dispatch_capabilities=DispatchCapabilities(supported=True, version=4),
    )
    mock_register_service.read_all.return_value = {HOLDING_START + offset: 0 for offset in range(HOLDING_COUNT)}

    data = await coordinator._async_update_data()

    assert data.remote_dispatch is None


async def test_async_update_data_register_service_error(
    hass: HomeAssistant,
    coordinator: SolisCloudControlCoordinator,
    mock_register_service: AsyncMock,
) -> None:
    any_error = "any register error"
    mock_register_service.read_all.side_effect = RegisterServiceError(any_error)

    with pytest.raises(UpdateFailed) as exc_info:
        await coordinator._async_update_data()

    assert str(exc_info.value) == any_error


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


async def test_control_preserves_remote_dispatch(
    coordinator: SolisCloudControlCoordinator, mock_cid_service: AsyncMock
) -> None:
    any_cid = 123
    any_value = "any_value"
    remote_dispatch = RemoteDispatch(DispatchCapabilities(supported=True, version=3))

    coordinator.data = SolisCloudControlData(cids={any_cid: "initial_value"}, remote_dispatch=remote_dispatch)

    with (
        patch.object(coordinator, "async_request_refresh", AsyncMock()) as mock_request_refresh,
        patch.object(coordinator, "async_set_updated_data", Mock()) as mock_set_updated_data,
    ):
        await coordinator.control(any_cid, any_value)

        mock_set_updated_data.assert_called_once_with(
            SolisCloudControlData(cids={any_cid: any_value}, remote_dispatch=remote_dispatch)
        )
        mock_cid_service.control.assert_awaited_once_with(any_cid, any_value, None)
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
