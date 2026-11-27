from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, cast

import pytest
from aiohttp import ClientSession, web
from aiohttp.test_utils import TestClient

from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient
from custom_components.solis_cloud_control.api.solis_api_error import (
    SolisCloudControlApiError,
    SolisCloudControlPermanentApiError,
    SolisCloudControlTransientApiError,
)

if TYPE_CHECKING:
    from pytest_aiohttp.plugin import AiohttpClient

type ApiClientFactory = Callable[[TestClient[web.Request, web.Application]], SolisCloudControlApiClient]
type MockEndpoint = Callable[[web.Request], Awaitable[web.Response]]


@pytest.fixture
def create_api_client() -> ApiClientFactory:
    def _create_api_client(client: TestClient[web.Request, web.Application]) -> SolisCloudControlApiClient:
        return SolisCloudControlApiClient(
            base_url="",
            api_key="any key",
            api_token="any token",
            # TestClient proxies requests to its session, which is all the API client needs
            session=cast("ClientSession", client),
        )

    return _create_api_client


async def test_read(create_api_client: ApiClientFactory, aiohttp_client: AiohttpClient) -> None:
    any_inverter_sn = "any inverter sn"
    any_cid = -1
    any_result = "any result"

    async def mock_read_endpoint(request: web.Request) -> web.Response:
        body = await request.json()
        assert body.get("inverterSn") == any_inverter_sn
        assert body.get("cid") == any_cid
        return web.json_response({"code": "0", "msg": "Success", "data": {"msg": any_result}})

    app = web.Application()
    app.router.add_route("POST", SolisCloudControlApiClient._READ_ENDPOINT, mock_read_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    result = await api_client.read(inverter_sn=any_inverter_sn, cid=any_cid, max_retry_time=0)

    assert result == any_result


async def test_read_batch(create_api_client: ApiClientFactory, aiohttp_client: AiohttpClient) -> None:
    any_inverter_sn = "any inverter sn"
    any_cids = [-1, -2, -3]
    any_results = {-1: "any result 1", -2: "any result 2", -3: "any result 3"}

    async def mock_read_batch_endpoint(request: web.Request) -> web.Response:
        body = await request.json()
        assert body.get("inverterSn") == any_inverter_sn
        assert body.get("cids") == ",".join(map(str, any_cids))
        data = [[{"cid": cid, "msg": msg} for cid, msg in any_results.items()]]
        return web.json_response({"code": "0", "msg": "Success", "data": data})

    app = web.Application()
    app.router.add_route("POST", SolisCloudControlApiClient._READ_BATCH_ENDPOINT, mock_read_batch_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    result = await api_client.read_batch(inverter_sn=any_inverter_sn, cids=any_cids, max_retry_time=0)

    assert result == any_results


async def test_read_registers(create_api_client: ApiClientFactory, aiohttp_client: AiohttpClient) -> None:
    any_inverter_sn = "any inverter sn"
    any_addr = -1
    any_function_code = "04"
    any_register_number = 3
    any_values = [0, 5, 65535]

    async def mock_read_registers_endpoint(request: web.Request) -> web.Response:
        body = await request.json()
        assert body.get("inverterSn") == any_inverter_sn
        assert body.get("modbusAddr") == any_addr
        assert body.get("functionCode") == any_function_code
        assert body.get("registerNumber") == any_register_number
        detail = [{"values": any_values, "value": ",".join(map(str, any_values))}]
        return web.json_response({"code": "0", "msg": "Success", "data": [{"code": "0", "detail": detail}]})

    app = web.Application()
    app.router.add_route("POST", SolisCloudControlApiClient._READ_ENDPOINT, mock_read_registers_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    result = await api_client.read_registers(
        inverter_sn=any_inverter_sn,
        addr=any_addr,
        function_code=any_function_code,
        register_number=any_register_number,
        max_retry_time=0,
    )

    assert result == any_values


async def test_read_registers_defaults(create_api_client: ApiClientFactory, aiohttp_client: AiohttpClient) -> None:
    any_inverter_sn = "any inverter sn"
    any_addr = -1

    async def mock_read_registers_endpoint(request: web.Request) -> web.Response:
        body = await request.json()
        assert body.get("functionCode") == "03"
        assert body.get("registerNumber") == 1
        return web.json_response({"code": "0", "msg": "Success", "data": [{"code": "0", "detail": [{"values": [5]}]}]})

    app = web.Application()
    app.router.add_route("POST", SolisCloudControlApiClient._READ_ENDPOINT, mock_read_registers_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    result = await api_client.read_registers(inverter_sn=any_inverter_sn, addr=any_addr, max_retry_time=0)

    assert result == [5]


async def test_control(create_api_client: ApiClientFactory, aiohttp_client: AiohttpClient) -> None:
    any_inverter_sn = "any inverter sn"
    any_cid = -1
    any_value = "any value"
    any_old_value = "any old value"

    async def mock_control_endpoint(request: web.Request) -> web.Response:
        body = await request.json()
        assert body.get("inverterSn") == any_inverter_sn
        assert body.get("cid") == any_cid
        assert body.get("value") == any_value
        assert body.get("yuanzhi") == any_old_value
        return web.json_response({"code": "0", "msg": "Success", "data": [{"code": "0", "msg": "Success"}]})

    app = web.Application()
    app.router.add_route("POST", SolisCloudControlApiClient._CONTROL_ENDPOINT, mock_control_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    await api_client.control(
        inverter_sn=any_inverter_sn, cid=any_cid, value=any_value, old_value=any_old_value, max_retry_time=0
    )


async def test_inverter_list(create_api_client: ApiClientFactory, aiohttp_client: AiohttpClient) -> None:
    any_records = [
        {"field 1": "record 1, value 1", "field2": "record 1, value 2"},
        {"field 1": "record 2, value 1", "field 2": "record 2, value 2"},
    ]

    async def mock_inverter_list_endpoint(request: web.Request) -> web.Response:
        body = await request.json()
        assert body.get("pageSize") == "100"
        return web.json_response({"code": "0", "msg": "Success", "data": {"page": {"records": any_records}}})

    app = web.Application()
    app.router.add_route("POST", SolisCloudControlApiClient._INVERTER_LIST_ENDPOINT, mock_inverter_list_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    result = await api_client.inverter_list(max_retry_time=0)

    assert result == any_records


async def test_inverter_details(create_api_client: ApiClientFactory, aiohttp_client: AiohttpClient) -> None:
    any_inverter_sn = "any_inverter_sn"
    any_details_response = {"field1": "value1", "field2": "value2"}

    async def mock_inverter_details_endpoint(request: web.Request) -> web.Response:
        body = await request.json()
        assert body.get("sn") == any_inverter_sn
        return web.json_response({"code": "0", "msg": "Success", "data": any_details_response})

    app = web.Application()
    app.router.add_route("POST", SolisCloudControlApiClient._INVERTER_DETAILS_ENDPOINT, mock_inverter_details_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    result = await api_client.inverter_details(inverter_sn=any_inverter_sn, max_retry_time=0)

    assert result == any_details_response


async def mock_read_endpoint_http_error(request: web.Request) -> web.Response:
    return web.Response(status=500, text="Internal Server Error")


async def mock_read_endpoint_api_error(request: web.Request) -> web.Response:
    return web.json_response({"code": "100", "msg": "API Error"})


async def mock_read_endpoint_missing_data_field(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success"})


async def mock_read_endpoint_missing_msg_field(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success", "data": {"unknown field": "any value"}})


@pytest.mark.parametrize(
    "mock_endpoint,expected_error",
    [
        (mock_read_endpoint_http_error, SolisCloudControlTransientApiError("Internal Server Error", status_code=500)),
        (
            mock_read_endpoint_api_error,
            SolisCloudControlPermanentApiError("API operation failed: API Error", response_code="100"),
        ),
        (
            mock_read_endpoint_missing_data_field,
            SolisCloudControlPermanentApiError("Read failed: missing 'data' field"),
        ),
        (
            mock_read_endpoint_missing_msg_field,
            SolisCloudControlPermanentApiError("Read failed: missing 'msg' field"),
        ),
    ],
)
async def test_read_errors(
    mock_endpoint: MockEndpoint,
    expected_error: SolisCloudControlApiError,
    create_api_client: ApiClientFactory,
    aiohttp_client: AiohttpClient,
) -> None:
    app = web.Application()
    app.router.add_route("POST", SolisCloudControlApiClient._READ_ENDPOINT, mock_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    with pytest.raises(type(expected_error)) as excinfo:
        await api_client.read(inverter_sn="any inverter", cid=-1, max_retry_time=0)

    assert str(excinfo.value) == str(expected_error)


async def mock_read_batch_endpoint_http_error(request: web.Request) -> web.Response:
    return web.Response(status=500, text="Internal Server Error")


async def mock_read_batch_endpoint_api_error(request: web.Request) -> web.Response:
    return web.json_response({"code": "100", "msg": "API Error"})


async def mock_read_batch_endpoint_missing_data_field(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success"})


async def mock_read_batch_endpoint_invalid_data_format(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success", "data": "not an array"})


async def mock_read_batch_endpoint_invalid_outer_data_format(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success", "data": ["not an array"]})


async def mock_read_batch_endpoint_missing_msg_field(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success", "data": [[{"cid": -1}]]})


async def mock_read_batch_endpoint_missing_cid_field(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success", "data": [[{"msg": "any message"}]]})


@pytest.mark.parametrize(
    "mock_endpoint,expected_error",
    [
        (
            mock_read_batch_endpoint_http_error,
            SolisCloudControlTransientApiError("Internal Server Error", status_code=500),
        ),
        (
            mock_read_batch_endpoint_api_error,
            SolisCloudControlPermanentApiError("API operation failed: API Error", response_code="100"),
        ),
        (
            mock_read_batch_endpoint_missing_data_field,
            SolisCloudControlPermanentApiError("ReadBatch failed: missing 'data' field"),
        ),
        (
            mock_read_batch_endpoint_invalid_data_format,
            SolisCloudControlPermanentApiError("ReadBatch failed: 'data' field is not an array"),
        ),
        (
            mock_read_batch_endpoint_invalid_outer_data_format,
            SolisCloudControlPermanentApiError("ReadBatch failed: 'data' field element is not an array"),
        ),
        (
            mock_read_batch_endpoint_missing_msg_field,
            SolisCloudControlPermanentApiError("ReadBatch failed: missing 'msg' field"),
        ),
        (
            mock_read_batch_endpoint_missing_cid_field,
            SolisCloudControlPermanentApiError("ReadBatch failed: missing 'cid' field"),
        ),
    ],
)
async def test_read_batch_errors(
    mock_endpoint: MockEndpoint,
    expected_error: SolisCloudControlApiError,
    create_api_client: ApiClientFactory,
    aiohttp_client: AiohttpClient,
) -> None:
    app = web.Application()
    app.router.add_route("POST", SolisCloudControlApiClient._READ_BATCH_ENDPOINT, mock_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    with pytest.raises(type(expected_error)) as excinfo:
        await api_client.read_batch(inverter_sn="any inverter", cids=[-1], max_retry_time=0)

    assert str(excinfo.value) == str(expected_error)


async def mock_read_registers_endpoint_http_error(request: web.Request) -> web.Response:
    return web.Response(status=500, text="Internal Server Error")


async def mock_read_registers_endpoint_api_error(request: web.Request) -> web.Response:
    return web.json_response({"code": "100", "msg": "API Error"})


async def mock_read_registers_endpoint_register_error(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success", "data": [{"code": "100", "msg": "Any Error"}]})


async def mock_read_registers_endpoint_transient_register_error(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success", "data": [{"code": "B0250", "msg": "Device busy"}]})


async def mock_read_registers_endpoint_missing_data_field(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success"})


async def mock_read_registers_endpoint_invalid_data_format(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success", "data": "not an array"})


async def mock_read_registers_endpoint_empty_data(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success", "data": []})


async def mock_read_registers_endpoint_invalid_data_element(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success", "data": ["not an object"]})


async def mock_read_registers_endpoint_missing_detail_field(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success", "data": [{"code": "0"}]})


async def mock_read_registers_endpoint_empty_detail_field(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success", "data": [{"code": "0", "detail": []}]})


async def mock_read_registers_endpoint_invalid_detail_element(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success", "data": [{"code": "0", "detail": ["not an object"]}]})


async def mock_read_registers_endpoint_missing_values_field(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success", "data": [{"code": "0", "detail": [{"value": "1"}]}]})


async def mock_read_registers_endpoint_short_values(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success", "data": [{"code": "0", "detail": [{"values": [1]}]}]})


@pytest.mark.parametrize(
    "mock_endpoint,expected_error",
    [
        (
            mock_read_registers_endpoint_http_error,
            SolisCloudControlTransientApiError("Internal Server Error", status_code=500),
        ),
        (
            mock_read_registers_endpoint_api_error,
            SolisCloudControlPermanentApiError("API operation failed: API Error", response_code="100"),
        ),
        (
            mock_read_registers_endpoint_register_error,
            SolisCloudControlPermanentApiError("ReadRegisters failed: Any Error", response_code="100"),
        ),
        (
            mock_read_registers_endpoint_transient_register_error,
            SolisCloudControlTransientApiError("ReadRegisters failed: Device busy", response_code="B0250"),
        ),
        (
            mock_read_registers_endpoint_missing_data_field,
            SolisCloudControlPermanentApiError("ReadRegisters failed: missing 'data' field"),
        ),
        (
            mock_read_registers_endpoint_invalid_data_format,
            SolisCloudControlPermanentApiError("ReadRegisters failed: 'data' field is not an array"),
        ),
        (
            mock_read_registers_endpoint_empty_data,
            SolisCloudControlPermanentApiError("ReadRegisters failed: empty 'data' array"),
        ),
        (
            mock_read_registers_endpoint_invalid_data_element,
            SolisCloudControlPermanentApiError("ReadRegisters failed: invalid 'data' element"),
        ),
        (
            mock_read_registers_endpoint_missing_detail_field,
            SolisCloudControlPermanentApiError("ReadRegisters failed: missing 'detail' field"),
        ),
        (
            mock_read_registers_endpoint_empty_detail_field,
            SolisCloudControlPermanentApiError("ReadRegisters failed: empty 'detail' array"),
        ),
        (
            mock_read_registers_endpoint_invalid_detail_element,
            SolisCloudControlPermanentApiError("ReadRegisters failed: invalid 'detail' element"),
        ),
        (
            mock_read_registers_endpoint_missing_values_field,
            SolisCloudControlPermanentApiError("ReadRegisters failed: missing 'values' field"),
        ),
        (
            mock_read_registers_endpoint_short_values,
            SolisCloudControlPermanentApiError("ReadRegisters failed: expected 2 values, got 1"),
        ),
    ],
)
async def test_read_registers_errors(
    mock_endpoint: MockEndpoint,
    expected_error: SolisCloudControlApiError,
    create_api_client: ApiClientFactory,
    aiohttp_client: AiohttpClient,
) -> None:
    app = web.Application()
    app.router.add_route("POST", SolisCloudControlApiClient._READ_ENDPOINT, mock_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    with pytest.raises(type(expected_error)) as excinfo:
        await api_client.read_registers(inverter_sn="any inverter", addr=-1, register_number=2, max_retry_time=0)

    assert str(excinfo.value) == str(expected_error)


async def mock_control_endpoint_http_error(request: web.Request) -> web.Response:
    return web.Response(status=500, text="Internal Server Error")


async def mock_control_endpoint_api_error(request: web.Request) -> web.Response:
    return web.json_response({"code": "100", "msg": "API Error"})


async def mock_control_endpoint_control_error(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success", "data": [{"code": "100", "msg": "Any Error"}]})


async def mock_control_endpoint_missing_data_field(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success"})


async def mock_control_endpoint_invalid_data_format(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success", "data": "not an array"})


@pytest.mark.parametrize(
    "mock_endpoint,expected_error",
    [
        (
            mock_control_endpoint_http_error,
            SolisCloudControlTransientApiError("Internal Server Error", status_code=500),
        ),
        (
            mock_control_endpoint_api_error,
            SolisCloudControlPermanentApiError("API operation failed: API Error", response_code="100"),
        ),
        (
            mock_control_endpoint_control_error,
            SolisCloudControlPermanentApiError("Control failed: Any Error", response_code="100"),
        ),
        (
            mock_control_endpoint_missing_data_field,
            SolisCloudControlPermanentApiError("Control failed: missing 'data' field"),
        ),
        (
            mock_control_endpoint_invalid_data_format,
            SolisCloudControlPermanentApiError("Control failed: 'data' field is not an array"),
        ),
    ],
)
async def test_control_errors(
    mock_endpoint: MockEndpoint,
    expected_error: SolisCloudControlApiError,
    create_api_client: ApiClientFactory,
    aiohttp_client: AiohttpClient,
) -> None:
    app = web.Application()
    app.router.add_route("POST", SolisCloudControlApiClient._CONTROL_ENDPOINT, mock_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    with pytest.raises(type(expected_error)) as excinfo:
        await api_client.control(inverter_sn="any inverter", cid=-1, value="any value", max_retry_time=0)

    assert str(excinfo.value) == str(expected_error)


async def mock_inverter_list_endpoint_missing_data_field(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success"})


async def mock_inverter_list_endpoint_missing_page(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success", "data": {}})


async def mock_inverter_list_endpoint_missing_records(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success", "data": {"page": {}}})


@pytest.mark.parametrize(
    "mock_endpoint,expected_error",
    [
        (mock_read_endpoint_http_error, SolisCloudControlTransientApiError("Internal Server Error", status_code=500)),
        (
            mock_read_endpoint_api_error,
            SolisCloudControlPermanentApiError("API operation failed: API Error", response_code="100"),
        ),
        (
            mock_inverter_list_endpoint_missing_data_field,
            SolisCloudControlPermanentApiError("InverterList failed: missing 'data' field"),
        ),
        (
            mock_inverter_list_endpoint_missing_page,
            SolisCloudControlPermanentApiError("InverterList failed: missing 'page' field"),
        ),
        (
            mock_inverter_list_endpoint_missing_records,
            SolisCloudControlPermanentApiError("InverterList failed: missing 'records' field"),
        ),
    ],
)
async def test_inverter_list_errors(
    mock_endpoint: MockEndpoint,
    expected_error: SolisCloudControlApiError,
    create_api_client: ApiClientFactory,
    aiohttp_client: AiohttpClient,
) -> None:
    app = web.Application()
    app.router.add_route("POST", SolisCloudControlApiClient._INVERTER_LIST_ENDPOINT, mock_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    with pytest.raises(type(expected_error)) as excinfo:
        await api_client.inverter_list(max_retry_time=0)

    assert str(excinfo.value) == str(expected_error)


async def mock_inverter_details_endpoint_missing_data_field(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success"})


@pytest.mark.parametrize(
    "mock_endpoint,expected_error",
    [
        (mock_read_endpoint_http_error, SolisCloudControlTransientApiError("Internal Server Error", status_code=500)),
        (
            mock_read_endpoint_api_error,
            SolisCloudControlPermanentApiError("API operation failed: API Error", response_code="100"),
        ),
        (
            mock_inverter_details_endpoint_missing_data_field,
            SolisCloudControlPermanentApiError("InverterDetails failed: missing 'data' field"),
        ),
    ],
)
async def test_inverter_details_errors(
    mock_endpoint: MockEndpoint,
    expected_error: SolisCloudControlApiError,
    create_api_client: ApiClientFactory,
    aiohttp_client: AiohttpClient,
) -> None:
    app = web.Application()
    app.router.add_route("POST", SolisCloudControlApiClient._INVERTER_DETAILS_ENDPOINT, mock_endpoint)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    with pytest.raises(type(expected_error)) as excinfo:
        await api_client.inverter_details(inverter_sn="any_inverter_sn", max_retry_time=0)

    assert str(excinfo.value) == str(expected_error)


async def mock_read_endpoint_disconnect(request: web.Request) -> web.Response:
    assert request.transport is not None
    request.transport.close()
    return web.Response()


async def mock_read_endpoint_success(request: web.Request) -> web.Response:
    return web.json_response({"code": "0", "msg": "Success", "data": {"msg": "any result"}})


async def test_read_connection_error_is_transient(
    create_api_client: ApiClientFactory, aiohttp_client: AiohttpClient
) -> None:
    app = web.Application()
    app.router.add_route("POST", SolisCloudControlApiClient._READ_ENDPOINT, mock_read_endpoint_disconnect)

    client = await aiohttp_client(app)
    api_client = create_api_client(client)

    with pytest.raises(SolisCloudControlTransientApiError):
        await api_client.read(inverter_sn="any inverter", cid=-1, max_retry_time=0)


async def test_read_timeout_is_transient(aiohttp_client: AiohttpClient) -> None:
    app = web.Application()
    app.router.add_route("POST", SolisCloudControlApiClient._READ_ENDPOINT, mock_read_endpoint_success)

    client = await aiohttp_client(app)
    api_client = SolisCloudControlApiClient(
        base_url="",
        api_key="any key",
        api_token="any token",
        session=cast("ClientSession", client),
        timeout=0,
    )

    with pytest.raises(SolisCloudControlTransientApiError):
        await api_client.read(inverter_sn="any inverter", cid=-1, max_retry_time=0)
