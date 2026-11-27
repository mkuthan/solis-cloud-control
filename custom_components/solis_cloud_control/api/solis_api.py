import asyncio
import json
import logging
from typing import Any

import aiohttp

from custom_components.solis_cloud_control.api.solis_api_error import (
    SolisCloudControlApiError,
    SolisCloudControlPermanentApiError,
    SolisCloudControlTransientApiError,
)
from custom_components.solis_cloud_control.api.solis_api_utils import (
    current_date,
    digest,
    format_date,
    sign_authorization,
)
from custom_components.solis_cloud_control.utils.retry_policy import RetryPolicy

_LOGGER = logging.getLogger(__name__)


class SolisCloudControlApiClient:
    _READ_ENDPOINT = "/v2/api/atRead"
    _READ_BATCH_ENDPOINT = "/v2/api/atReadBatch"
    _CONTROL_ENDPOINT = "/v2/api/control"
    _INVERTER_LIST_ENDPOINT = "/v1/api/inverterList"
    _INVERTER_DETAILS_ENDPOINT = "/v1/api/inverterDetail"
    _TIMEOUT_SECONDS = 30
    _CONCURRENT_REQUESTS = 1
    _MAX_RETRY_TIME_SECONDS = 30

    _RETRY_POLICY = RetryPolicy(retryable_exception=SolisCloudControlTransientApiError)

    def __init__(
        self,
        base_url: str,
        api_key: str,
        api_token: str,
        session: aiohttp.ClientSession,
        timeout: int = _TIMEOUT_SECONDS,
        retry_policy: RetryPolicy = _RETRY_POLICY,
        concurrent_requests: int = _CONCURRENT_REQUESTS,
    ) -> None:
        self._base_url = base_url
        self._api_key = api_key
        self._api_secret = api_token
        self._session = session
        self._timeout = timeout
        self._retry_policy = retry_policy
        self._request_semaphore = asyncio.Semaphore(concurrent_requests)

    async def read(self, inverter_sn: str, cid: int, max_retry_time: float = _MAX_RETRY_TIME_SECONDS) -> str:
        async def read_operation() -> str:
            payload = {"inverterSn": inverter_sn, "cid": cid}
            data = await self._execute_request(self._READ_ENDPOINT, payload)

            if data is None:
                raise SolisCloudControlPermanentApiError("Read failed: missing 'data' field")

            if "msg" not in data:
                raise SolisCloudControlPermanentApiError("Read failed: missing 'msg' field")

            return data["msg"]

        return await self._retry_policy(read_operation, max_retry_time)

    async def read_batch(
        self,
        inverter_sn: str,
        cids: list[int],
        max_retry_time: float = _MAX_RETRY_TIME_SECONDS,
    ) -> dict[int, str]:
        async def read_batch_operation() -> dict[int, str]:
            payload = {"inverterSn": inverter_sn, "cids": ",".join(map(str, cids))}

            data = await self._execute_request(self._READ_BATCH_ENDPOINT, payload)

            if data is None:
                raise SolisCloudControlPermanentApiError("ReadBatch failed: missing 'data' field")

            if not isinstance(data, list):
                raise SolisCloudControlPermanentApiError("ReadBatch failed: 'data' field is not an array")

            result = {}
            for outer_item in data:
                if not isinstance(outer_item, list):
                    raise SolisCloudControlPermanentApiError("ReadBatch failed: 'data' field element is not an array")

                for item in outer_item:
                    if "msg" not in item:
                        raise SolisCloudControlPermanentApiError("ReadBatch failed: missing 'msg' field")
                    if "cid" not in item:
                        raise SolisCloudControlPermanentApiError("ReadBatch failed: missing 'cid' field")

                    result[int(item["cid"])] = item["msg"]

            return result

        return await self._retry_policy(read_batch_operation, max_retry_time)

    async def read_registers(
        self,
        inverter_sn: str,
        addr: int,
        function_code: str = "03",
        register_number: int = 1,
        max_retry_time: float = _MAX_RETRY_TIME_SECONDS,
    ) -> list[int]:
        async def read_operation() -> list[int]:
            payload = {
                "inverterSn": inverter_sn,
                "modbusAddr": addr,
                "functionCode": function_code,
                "registerNumber": register_number,
            }
            data_array = await self._execute_request(self._READ_ENDPOINT, payload)

            if data_array is None:
                raise SolisCloudControlPermanentApiError("ReadRegisters failed: missing 'data' field")

            if not isinstance(data_array, list):
                raise SolisCloudControlPermanentApiError("ReadRegisters failed: 'data' field is not an array")

            if not data_array:
                raise SolisCloudControlPermanentApiError("ReadRegisters failed: empty 'data' array")

            data = data_array[0]
            if not isinstance(data, dict):
                raise SolisCloudControlPermanentApiError("ReadRegisters failed: invalid 'data' element")

            code = data.get("code")
            if code is not None and str(code) != "0":
                error_msg = data.get("msg", "Unknown error")
                raise SolisCloudControlApiError.create(f"ReadRegisters failed: {error_msg}", response_code=str(code))

            detail = data.get("detail")
            if not isinstance(detail, list):
                raise SolisCloudControlPermanentApiError("ReadRegisters failed: missing 'detail' field")

            if not detail:
                raise SolisCloudControlPermanentApiError("ReadRegisters failed: empty 'detail' array")

            if not isinstance(detail[0], dict):
                raise SolisCloudControlPermanentApiError("ReadRegisters failed: invalid 'detail' element")

            values = detail[0].get("values")
            if not isinstance(values, list):
                raise SolisCloudControlPermanentApiError("ReadRegisters failed: missing 'values' field")

            if len(values) != register_number:
                raise SolisCloudControlPermanentApiError(
                    f"ReadRegisters failed: expected {register_number} values, got {len(values)}"
                )

            return [int(value) for value in values]

        return await self._retry_policy(read_operation, max_retry_time)

    async def control(
        self,
        inverter_sn: str,
        cid: int,
        value: str,
        old_value: str | None = None,
        max_retry_time: float = _MAX_RETRY_TIME_SECONDS,
    ) -> None:
        async def control_operation() -> None:
            payload = {"inverterSn": inverter_sn, "cid": cid, "value": value}
            if old_value is not None:
                payload["yuanzhi"] = old_value

            data_array = await self._execute_request(self._CONTROL_ENDPOINT, payload)

            if data_array is None:
                raise SolisCloudControlPermanentApiError("Control failed: missing 'data' field")

            if not isinstance(data_array, list):
                raise SolisCloudControlPermanentApiError("Control failed: 'data' field is not an array")

            for data in data_array:
                code = data.get("code")

                if code is not None and str(code) != "0":
                    error_msg = data.get("msg", "Unknown error")
                    raise SolisCloudControlApiError.create(f"Control failed: {error_msg}", response_code=str(code))

            return

        return await self._retry_policy(control_operation, max_retry_time)

    async def inverter_list(
        self,
        max_retry_time: float = _MAX_RETRY_TIME_SECONDS,
    ) -> list[dict]:
        async def inverter_list_operation() -> list[dict]:
            payload = {"pageSize": "100"}
            data = await self._execute_request(self._INVERTER_LIST_ENDPOINT, payload)

            if data is None:
                raise SolisCloudControlPermanentApiError("InverterList failed: missing 'data' field")

            if "page" not in data:
                raise SolisCloudControlPermanentApiError("InverterList failed: missing 'page' field")

            if "records" not in data["page"]:
                raise SolisCloudControlPermanentApiError("InverterList failed: missing 'records' field")

            return data["page"]["records"]

        return await self._retry_policy(inverter_list_operation, max_retry_time)

    async def inverter_details(
        self,
        inverter_sn: str,
        max_retry_time: float = _MAX_RETRY_TIME_SECONDS,
    ) -> dict:
        async def inverter_details_operation() -> dict:
            payload = {"sn": inverter_sn}
            data = await self._execute_request(self._INVERTER_DETAILS_ENDPOINT, payload)

            if data is None:
                raise SolisCloudControlPermanentApiError("InverterDetails failed: missing 'data' field")

            return data

        return await self._retry_policy(inverter_details_operation, max_retry_time)

    async def _execute_request(self, endpoint: str, payload: dict | None = None) -> Any:  # noqa: ANN401
        body = json.dumps(payload)

        payload_digest = digest(body)
        content_type = "application/json"

        date = current_date()
        date_formatted = format_date(date)

        authorization_str = "\n".join(["POST", payload_digest, content_type, date_formatted, endpoint])

        authorization_sign = sign_authorization(self._api_secret, authorization_str)

        authorization = f"API {self._api_key}:{authorization_sign}"

        headers = {
            "Content-MD5": payload_digest,
            "Content-Type": content_type,
            "Date": date_formatted,
            "Authorization": authorization,
        }

        url = f"{self._base_url}{endpoint}"

        _LOGGER.debug("API request '%s': %s", endpoint, json.dumps(payload, indent=2))

        try:
            async with asyncio.timeout(self._timeout):
                async with self._request_semaphore:
                    async with self._session.post(url, headers=headers, json=payload) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise SolisCloudControlApiError.create(error_text, status_code=response.status)

                        response_json = await response.json()

                        _LOGGER.debug("API response: %s", json.dumps(response_json, indent=2))

                        code = response_json.get("code", "Unknown code")
                        if str(code) != "0":
                            error_msg = response_json.get("msg", "Unknown error")
                            raise SolisCloudControlApiError.create(
                                f"API operation failed: {error_msg}", response_code=str(code)
                            )

                        return response_json.get("data")
        except TimeoutError as err:
            raise SolisCloudControlTransientApiError(f"Timeout accessing {url}") from err
        except aiohttp.ClientError as err:
            raise SolisCloudControlTransientApiError(f"Error accessing {url}: {str(err)}") from err
