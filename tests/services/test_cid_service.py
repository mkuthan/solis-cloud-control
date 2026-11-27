from typing import TYPE_CHECKING

import pytest

from custom_components.solis_cloud_control.api.solis_api_error import SolisCloudControlApiError
from custom_components.solis_cloud_control.services.cid_service import CidService, CidServiceError
from tests.helpers import assert_control

if TYPE_CHECKING:
    from unittest.mock import AsyncMock

    from custom_components.solis_cloud_control.inverters.inverter import Inverter


@pytest.fixture
def cid_service(mock_api_client: AsyncMock, any_inverter: Inverter) -> CidService:
    return CidService(mock_api_client, any_inverter)


async def test_read_all(cid_service: CidService, mock_api_client: AsyncMock, any_inverter: Inverter) -> None:
    mock_api_client.read_batch.side_effect = lambda _sn, cids, **_: {cid: f"value_{cid}" for cid in cids}
    mock_api_client.read.side_effect = lambda _sn, cid, **_: f"value_{cid}"

    data = await cid_service.read_all()

    serial_number = any_inverter.info.serial_number

    mock_api_client.read_batch.assert_awaited_once()
    batch_call = mock_api_client.read_batch.await_args
    batch_cids = batch_call.args[1]
    assert batch_call.args[0] == serial_number
    assert batch_call.kwargs == {"max_retry_time": 180}

    single_cids = [call.args[1] for call in mock_api_client.read.await_args_list]
    for call in mock_api_client.read.await_args_list:
        assert call.args[0] == serial_number
        assert call.kwargs == {"max_retry_time": 60}

    assert batch_cids
    assert single_cids
    assert data == {cid: f"value_{cid}" for cid in [*batch_cids, *single_cids]}


async def test_read_all_missing_values(cid_service: CidService, mock_api_client: AsyncMock) -> None:
    mock_api_client.read_batch.return_value = {}
    mock_api_client.read.return_value = None

    data = await cid_service.read_all()

    expected_cids = [*cid_service._read_batch_cids(), *cid_service._read_cids()]
    assert expected_cids
    assert data == dict.fromkeys(expected_cids)


async def test_read_all_api_error(cid_service: CidService, mock_api_client: AsyncMock, any_inverter: Inverter) -> None:
    any_error = "any error"
    any_api_error = SolisCloudControlApiError(any_error)
    mock_api_client.read_batch.side_effect = any_api_error

    with pytest.raises(CidServiceError) as exc_info:
        await cid_service.read_all()

    assert str(exc_info.value) == any_error
    assert exc_info.value.__cause__ is any_api_error
    mock_api_client.read_batch.assert_called_once_with(
        any_inverter.info.serial_number,
        cid_service._read_batch_cids(),
        max_retry_time=180,
    )
    mock_api_client.read.assert_not_called()


async def test_control(cid_service: CidService, mock_api_client: AsyncMock, any_inverter: Inverter) -> None:
    any_cid = 123
    any_value = "any_value"
    any_old_value = "any_old_value"

    mock_api_client.control.return_value = None

    await cid_service.control(any_cid, any_value, any_old_value)

    assert_control(mock_api_client, any_inverter, any_cid, any_value, any_old_value)


async def test_control_api_error(cid_service: CidService, mock_api_client: AsyncMock, any_inverter: Inverter) -> None:
    any_cid = 123
    any_value = "any_value"
    any_old_value = "any_old_value"
    any_error = "any error"

    any_api_error = SolisCloudControlApiError(any_error)
    mock_api_client.control.side_effect = any_api_error

    with pytest.raises(CidServiceError) as exc_info:
        await cid_service.control(any_cid, any_value, any_old_value)

    assert str(exc_info.value) == any_error
    assert exc_info.value.__cause__ is any_api_error
    assert_control(mock_api_client, any_inverter, any_cid, any_value, any_old_value)
