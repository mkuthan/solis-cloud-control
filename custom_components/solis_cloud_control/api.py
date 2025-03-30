import asyncio
import json
import logging

import aiohttp

from custom_components.solis_cloud_control.utils import current_date, digest, format_date, sign_authorization

from .const import (
    API_CONCURRENT_REQUESTS,
    API_CONTROL_ENDPOINT,
    API_READ_BATCH_ENDPOINT,
    API_READ_ENDPOINT,
    API_RETRY_COUNT,
    API_RETRY_DELAY_SECONDS,
    API_TIMEOUT_SECONDS,
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
    def __init__(
        self,
        base_url: str,
        api_key: str,
        api_token: str,
        session: aiohttp.ClientSession,
    ) -> None:
        self._base_url = base_url
        self._api_key = api_key
        self._api_secret = api_token
        self._session = session
        self._request_semaphore = asyncio.Semaphore(API_CONCURRENT_REQUESTS)

    async def _execute_request_with_retry(
        self,
        endpoint: str,
        payload: dict[str, any],
        retry_count: int = API_RETRY_COUNT,
        retry_delay: float = API_RETRY_DELAY_SECONDS,
    ) -> any:
        attempt = 0

        while attempt < retry_count:
            try:
                return await self._execute_request(endpoint, payload)
            except SolisCloudControlApiError as err:
                attempt += 1
                if attempt < retry_count:
                    _LOGGER.warning("Retrying due to error: %s (attempt %d/%d)", str(err), attempt, retry_count)
                    await asyncio.sleep(retry_delay)
                else:
                    raise

    async def _execute_request(self, endpoint: str, payload: dict[str, any] = None) -> any:
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
            async with asyncio.timeout(API_TIMEOUT_SECONDS):
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

    async def read(self, inverter_sn: str, cid: int) -> str:
        payload = {"inverterSn": inverter_sn, "cid": cid}

        data = await self._execute_request_with_retry(API_READ_ENDPOINT, payload)

        if data is None:
            raise SolisCloudControlApiError("Read failed: 'data' field is missing in response")

        if "msg" not in data:
            raise SolisCloudControlApiError("Read failed: 'msg' field is missing in response")

        return data["msg"]

    async def read_batch(self, inverter_sn: str, cids: list[int]) -> dict[int, str]:
        payload = {"inverterSn": inverter_sn, "cids": ",".join(map(str, cids))}

        data = await self._execute_request_with_retry(API_READ_BATCH_ENDPOINT, payload)

        if data is None:
            raise SolisCloudControlApiError("ReadBatch failed: 'data' field is missing in response")

        if not isinstance(data, list):
            raise SolisCloudControlApiError("ReadBatch failed: response data is not an array")

        result = {}
        for outer_item in data:
            if not isinstance(outer_item, list):
                continue

            for item in outer_item:
                if not isinstance(item, dict):
                    continue

                if "msg" not in item:
                    raise SolisCloudControlApiError("ReadBatch failed: 'msg' field is missing in response item")
                if "cid" not in item:
                    raise SolisCloudControlApiError("ReadBatch failed: 'cid' field is missing in response item")

                result[int(item["cid"])] = item["msg"]

        return result

    async def control(self, inverter_sn: str, cid: int, value: str, old_value: str | None = None) -> None:
        payload = {"inverterSn": inverter_sn, "cid": cid, "value": value}
        if old_value is not None:
            payload["yuanzhi"] = old_value

        data_array = await self._execute_request_with_retry(API_CONTROL_ENDPOINT, payload)

        if data_array is None:
            return

        if isinstance(data_array, list):
            for data in data_array:
                code = data.get("code")

                if code is not None and str(code) != "0":
                    error_msg = data.get("msg", "Unknown error")
                    raise SolisCloudControlApiError(f"Control failed: {error_msg}", response_code=str(code))

        return
