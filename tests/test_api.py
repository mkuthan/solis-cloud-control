from unittest.mock import patch

import pytest
from aiohttp import web

from custom_components.solis_cloud_control.api import SolisCloudControlApiClient, SolisCloudControlApiError
from custom_components.solis_cloud_control.const import API_READ_ENDPOINT


@pytest.fixture
def create_api_client():
    def _create_api_client(session):
        return SolisCloudControlApiClient(
            base_url="",
            api_key="any key",
            api_token="any token",
            session=session,
        )

    return _create_api_client


async def test_api_read(create_api_client, aiohttp_client):
    any_inverter_sn = "any inverter sn"
    any_cid = -1
    any_result = "any result"

    async def mock_read_endpoint(request):
        body = await request.json()
        assert body.get("inverterSn") == any_inverter_sn
        assert body.get("cid") == any_cid
        return web.json_response({"code": "0", "msg": "Success", "data": {"msg": any_result}})

    app = web.Application()
    app.router.add_route("POST", API_READ_ENDPOINT, mock_read_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    result = await api_client.read(inverter_sn=any_inverter_sn, cid=any_cid)

    assert result == any_result


async def mock_read_endpoint_api_error(request):
    return web.json_response({"code": "100", "msg": "API Error"})


async def mock_read_endpoint_missing_data_field(request):
    return web.json_response({"code": "0", "msg": "Success"})


async def mock_read_endpoint_missing_msg_field(request):
    return web.json_response({"code": "0", "msg": "Success", "data": {"unknown field": "any value"}})


async def mock_read_endpoint_http_error(request):
    return web.Response(status=500, text="Internal Server Error")


@pytest.fixture
def mock_retry_request():
    async def no_retry_request(request):
        return await request()

    with patch("custom_components.solis_cloud_control.api._retry_request", new=no_retry_request):
        yield


@pytest.fixture(
    params=[
        (mock_read_endpoint_http_error, SolisCloudControlApiError("Internal Server Error", status_code=500)),
        (
            mock_read_endpoint_api_error,
            SolisCloudControlApiError("API operation failed: API Error", response_code="100"),
        ),
        (
            mock_read_endpoint_missing_data_field,
            SolisCloudControlApiError("Read failed: 'data' field is missing in response"),
        ),
        (
            mock_read_endpoint_missing_msg_field,
            SolisCloudControlApiError("Read failed: 'msg' field is missing in response"),
        ),
    ]
)
async def test_api_read_errors(request, create_api_client, aiohttp_client, mock_retry_request) -> None:
    mock_endpoint, expected_error = request.param
    app = web.Application()
    app.router.add_route("POST", API_READ_ENDPOINT, mock_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    with pytest.raises(SolisCloudControlApiError) as excinfo:
        await api_client.read(inverter_sn="any inverter", cid=-1)

    assert str(excinfo.value) == str(expected_error)
