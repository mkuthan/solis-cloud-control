import pytest
from aiohttp import web

from custom_components.solis_cloud_control.api import (
    _CONTROL_ENDPOINT,
    _READ_BATCH_ENDPOINT,
    _READ_ENDPOINT,
    SolisCloudControlApiClient,
    SolisCloudControlApiError,
)


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
    app.router.add_route("POST", _READ_ENDPOINT, mock_read_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    result = await api_client.read(inverter_sn=any_inverter_sn, cid=any_cid)

    assert result == any_result


async def test_api_read_batch(create_api_client, aiohttp_client):
    any_inverter_sn = "any inverter sn"
    any_cids = [-1, -2, -3]
    any_results = {-1: "any result 1", -2: "any result 2", -3: "any result 3"}

    async def mock_read_batch_endpoint(request):
        body = await request.json()
        assert body.get("inverterSn") == any_inverter_sn
        assert body.get("cids") == ",".join(map(str, any_cids))
        data = [[{"cid": cid, "msg": msg} for cid, msg in any_results.items()]]
        return web.json_response({"code": "0", "msg": "Success", "data": data})

    app = web.Application()
    app.router.add_route("POST", _READ_BATCH_ENDPOINT, mock_read_batch_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    result = await api_client.read_batch(inverter_sn=any_inverter_sn, cids=any_cids)

    assert result == any_results


async def test_api_control(create_api_client, aiohttp_client):
    any_inverter_sn = "any inverter sn"
    any_cid = -1
    any_value = "any value"
    any_old_value = "any old value"

    async def mock_control_endpoint(request):
        body = await request.json()
        assert body.get("inverterSn") == any_inverter_sn
        assert body.get("cid") == any_cid
        assert body.get("value") == any_value
        assert body.get("yuanzhi") == any_old_value
        return web.json_response({"code": "0", "msg": "Success", "data": [{"code": "0", "msg": "Success"}]})

    app = web.Application()
    app.router.add_route("POST", _CONTROL_ENDPOINT, mock_control_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    await api_client.control(inverter_sn=any_inverter_sn, cid=any_cid, value=any_value, old_value=any_old_value)


async def mock_read_endpoint_http_error(request):
    return web.Response(status=500, text="Internal Server Error")


async def mock_read_endpoint_api_error(request):
    return web.json_response({"code": "100", "msg": "API Error"})


async def mock_read_endpoint_missing_data_field(request):
    return web.json_response({"code": "0", "msg": "Success"})


async def mock_read_endpoint_missing_msg_field(request):
    return web.json_response({"code": "0", "msg": "Success", "data": {"unknown field": "any value"}})


@pytest.mark.parametrize(
    "mock_endpoint,expected_error",
    [
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
    ],
)
async def test_api_read_errors(mock_endpoint, expected_error, create_api_client, aiohttp_client):
    app = web.Application()
    app.router.add_route("POST", _READ_ENDPOINT, mock_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    with pytest.raises(SolisCloudControlApiError) as excinfo:
        await api_client.read(inverter_sn="any inverter", cid=-1, retry_count=0)

    assert str(excinfo.value) == str(expected_error)


async def mock_read_batch_endpoint_http_error(request):
    return web.Response(status=500, text="Internal Server Error")


async def mock_read_batch_endpoint_api_error(request):
    return web.json_response({"code": "100", "msg": "API Error"})


async def mock_read_batch_endpoint_missing_data_field(request):
    return web.json_response({"code": "0", "msg": "Success"})


async def mock_read_batch_endpoint_invalid_data_format(request):
    return web.json_response({"code": "0", "msg": "Success", "data": "not an array"})


async def mock_read_batch_endpoint_invalid_outer_data_format(request):
    return web.json_response({"code": "0", "msg": "Success", "data": ["not an array"]})


async def mock_read_batch_endpoint_missing_msg_field(request):
    return web.json_response({"code": "0", "msg": "Success", "data": [[{"cid": -1}]]})


async def mock_read_batch_endpoint_missing_cid_field(request):
    return web.json_response({"code": "0", "msg": "Success", "data": [[{"msg": "any message"}]]})


@pytest.mark.parametrize(
    "mock_endpoint,expected_error",
    [
        (mock_read_batch_endpoint_http_error, SolisCloudControlApiError("Internal Server Error", status_code=500)),
        (
            mock_read_batch_endpoint_api_error,
            SolisCloudControlApiError("API operation failed: API Error", response_code="100"),
        ),
        (
            mock_read_batch_endpoint_missing_data_field,
            SolisCloudControlApiError("ReadBatch failed: 'data' field is missing in response"),
        ),
        (
            mock_read_batch_endpoint_invalid_data_format,
            SolisCloudControlApiError("ReadBatch failed: response data is not an array"),
        ),
        (
            mock_read_batch_endpoint_invalid_outer_data_format,
            SolisCloudControlApiError("ReadBatch failed: data outer item is not an array"),
        ),
        (
            mock_read_batch_endpoint_missing_msg_field,
            SolisCloudControlApiError("ReadBatch failed: 'msg' field is missing in response item"),
        ),
        (
            mock_read_batch_endpoint_missing_cid_field,
            SolisCloudControlApiError("ReadBatch failed: 'cid' field is missing in response item"),
        ),
    ],
)
async def test_api_read_batch_errors(mock_endpoint, expected_error, create_api_client, aiohttp_client):
    app = web.Application()
    app.router.add_route("POST", _READ_BATCH_ENDPOINT, mock_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    with pytest.raises(SolisCloudControlApiError) as excinfo:
        await api_client.read_batch(inverter_sn="any inverter", cids=[-1], retry_count=0)

    assert str(excinfo.value) == str(expected_error)


async def mock_control_endpoint_http_error(request):
    return web.Response(status=500, text="Internal Server Error")


async def mock_control_endpoint_api_error(request):
    return web.json_response({"code": "100", "msg": "API Error"})


async def mock_control_endpoint_control_error(request):
    return web.json_response({"code": "0", "msg": "Success", "data": [{"code": "100", "msg": "Any Error"}]})


async def mock_control_endpoint_missing_data_field(request):
    return web.json_response({"code": "0", "msg": "Success"})


async def mock_control_endpoint_invalid_data_format(request):
    return web.json_response({"code": "0", "msg": "Success", "data": "not an array"})


@pytest.mark.parametrize(
    "mock_endpoint,expected_error",
    [
        (mock_control_endpoint_http_error, SolisCloudControlApiError("Internal Server Error", status_code=500)),
        (
            mock_control_endpoint_api_error,
            SolisCloudControlApiError("API operation failed: API Error", response_code="100"),
        ),
        (
            mock_control_endpoint_control_error,
            SolisCloudControlApiError("Control failed: Any Error", response_code="100"),
        ),
        (
            mock_control_endpoint_missing_data_field,
            SolisCloudControlApiError("Control failed: 'data' field is missing in response"),
        ),
        (
            mock_control_endpoint_invalid_data_format,
            SolisCloudControlApiError("Control failed: response data is not an array"),
        ),
    ],
)
async def test_api_control_errors(mock_endpoint, expected_error, create_api_client, aiohttp_client):
    app = web.Application()
    app.router.add_route("POST", _CONTROL_ENDPOINT, mock_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    with pytest.raises(SolisCloudControlApiError) as excinfo:
        await api_client.control(inverter_sn="any inverter", cid=-1, value="any value", retry_count=0)

    assert str(excinfo.value) == str(expected_error)
