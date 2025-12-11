import asyncio
import json
import logging
import time

import aiohttp

from custom_components.solis_cloud_control.api.solis_api_utils import (
    current_date,
    digest,
    format_date,
    sign_authorization,
)

_LOGGER = logging.getLogger(__name__)


class SolisCloudControlApiError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_code: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.response_code = response_code
        final_message = message
        if status_code is not None:
            final_message = f"{final_message} (HTTP status code: {status_code})"
        if response_code is not None:
            final_message = f"{final_message} (API response code: {response_code})"

        super().__init__(final_message)


class SolisCloudControlApiClient:
    _READ_ENDPOINT = "/v2/api/atRead"
    _READ_BATCH_ENDPOINT = "/v2/api/atReadBatch"
    _CONTROL_ENDPOINT = "/v2/api/control"
    _INVERTER_LIST_ENDPOINT = "/v1/api/inverterList"
    _INVERTER_DETAILS_ENDPOINT = "/v1/api/inverterDetail"
    _TIMEOUT_SECONDS = 30
    _CONCURRENT_REQUESTS = 2
    _MAX_RETRY_TIME_SECONDS = 30
    _INITIAL_RETRY_DELAY_SECONDS = 1

    def __init__(
        self,
        base_url: str,
        api_key: str,
        api_token: str,
        session: aiohttp.ClientSession,
        timeout: int = _TIMEOUT_SECONDS,
        concurrent_requests: int = _CONCURRENT_REQUESTS,
    ) -> None:
        self._base_url = base_url
        self._api_key = api_key
        self._api_secret = api_token
        self._session = session
        self._timeout = timeout
        self._request_semaphore = asyncio.Semaphore(concurrent_requests)

    async def read(self, inverter_sn: str, cid: int, max_retry_time: float = _MAX_RETRY_TIME_SECONDS) -> str:
        async def read_operation() -> str:
            payload = {"inverterSn": inverter_sn, "cid": cid}
            data = await self._execute_request(self._READ_ENDPOINT, payload)

            if data is None:
                raise SolisCloudControlApiError("Read failed: missing 'data' field")

            if "msg" not in data:
                raise SolisCloudControlApiError("Read failed: missing 'msg' field")

            return data["msg"]

        return await self._with_retry(read_operation, max_retry_time)

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
                raise SolisCloudControlApiError("ReadBatch failed: missing 'data' field")

            if not isinstance(data, list):
                raise SolisCloudControlApiError("ReadBatch failed: 'data' field is not an array")

            result = {}
            for outer_item in data:
                if not isinstance(outer_item, list):
                    raise SolisCloudControlApiError("ReadBatch failed: 'data' field element is not an array")

                for item in outer_item:
                    if "msg" not in item:
                        raise SolisCloudControlApiError("ReadBatch failed: missing 'msg' field")
                    if "cid" not in item:
                        raise SolisCloudControlApiError("ReadBatch failed: missing 'cid' field")

                    result[int(item["cid"])] = item["msg"]

            return result

        return await self._with_retry(read_batch_operation, max_retry_time)

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
                raise SolisCloudControlApiError("Control failed: missing 'data' field")

            if not isinstance(data_array, list):
                raise SolisCloudControlApiError("Control failed: 'data' field is not an array")

            for data in data_array:
                code = data.get("code")

                if code is not None and str(code) != "0":
                    error_msg = data.get("msg", "Unknown error")
                    raise SolisCloudControlApiError(f"Control failed: {error_msg}", response_code=str(code))

            return

        return await self._with_retry(control_operation, max_retry_time)

    async def inverter_list(
        self,
        max_retry_time: float = _MAX_RETRY_TIME_SECONDS,
    ) -> list[dict]:
        async def inverter_list_operation() -> list[dict]:
            payload = {"pageSize": "100"}
            data = await self._execute_request(self._INVERTER_LIST_ENDPOINT, payload)

            if data is None:
                raise SolisCloudControlApiError("InverterList failed: missing 'data' field")

            if "page" not in data:
                raise SolisCloudControlApiError("InverterList failed: missing 'page' field")

            if "records" not in data["page"]:
                raise SolisCloudControlApiError("InverterList failed: missing 'records' field")

            return data["page"]["records"]

        return await self._with_retry(inverter_list_operation, max_retry_time)

    async def inverter_details(
        self,
        inverter_sn: str,
        max_retry_time: float = _MAX_RETRY_TIME_SECONDS,
    ) -> dict:
        async def inverter_details_operation() -> dict:
            payload = {"sn": inverter_sn}
            data = await self._execute_request(self._INVERTER_DETAILS_ENDPOINT, payload)

            if data is None:
                raise SolisCloudControlApiError("InverterDetails failed: missing 'data' field")

            return data

        return await self._with_retry(inverter_details_operation, max_retry_time)

    async def _execute_request(self, endpoint: str, payload: dict | None = None) -> any:
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
                            raise SolisCloudControlApiError(error_text, status_code=response.status)

                        response_json = await response.json()

                        _LOGGER.debug("API response: %s", json.dumps(response_json, indent=2))

                        code = response_json.get("code", "Unknown code")
                        if str(code) != "0":
                            error_msg = response_json.get("msg", "Unknown error")
                            raise SolisCloudControlApiError(f"API operation failed: {error_msg}", response_code=code)

                        return response_json.get("data")
        except TimeoutError as err:
            raise SolisCloudControlApiError(f"Timeout accessing {url}") from err
        except aiohttp.ClientError as err:
            raise SolisCloudControlApiError(f"Error accessing {url}: {str(err)}") from err

    async def _with_retry(
        self,
        operation_closure: callable,
        max_retry_time: float,
    ) -> any:
        start_time = time.monotonic()
        attempt = 0
        delay = self._INITIAL_RETRY_DELAY_SECONDS

        while True:
            try:
                return await operation_closure()
            except SolisCloudControlApiError as err:
                elapsed_time = time.monotonic() - start_time

                if elapsed_time >= max_retry_time:
                    raise err

                attempt += 1
                _LOGGER.warning(
                    "Retrying due to error: %s (attempt %d, elapsed time: %.1fs)",
                    str(err),
                    attempt,
                    elapsed_time,
                )

                await asyncio.sleep(delay)
                delay = min(delay * 2, max_retry_time - elapsed_time)
