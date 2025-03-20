import asyncio
import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime

import aiohttp

from custom_components.solis_cloud_control.utils import current_date, digest, sign_authorization

from .const import API_BASE_URL, API_TIMEOUT_SECONDS, CONTROL_ENDPOINT, LOGGER, READ_ENDPOINT


class SolisCloudControlApiError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_code: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.response_code = response_code
        super().__init__(message)


class SolisCloudControlApiClient:
    def __init__(
        self,
        api_key: str,
        api_token: str,
        inverter_sn: str,
        session: aiohttp.ClientSession,
    ) -> None:
        self._api_key = api_key
        self._api_secret = api_token
        self._inverter_sn = inverter_sn
        self._session = session

    async def _request(self, endpoint: str, payload: dict[str, any] = None) -> dict[str, any]:
        body = json.dumps(payload)

        payload_digest = digest(body)
        content_type = "application/json"
        date = current_date()

        authorization_str = "\n".join(["POST", payload_digest, content_type, date, endpoint])

        authorization_sign = sign_authorization(self._api_secret, authorization_str)

        authorization = f"API {self._api_key}:{authorization_sign}"

        headers = {
            "Content-MD5": payload_digest,
            "Content-Type": content_type,
            "Date": date,
            "Authorization": authorization,
        }

        url = f"{API_BASE_URL}{endpoint}"

        try:
            async with asyncio.timeout(API_TIMEOUT_SECONDS):
                async with self._session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise SolisCloudControlApiError(error_text, status_code=response.status)

                    response_json = await response.json()

                    LOGGER.debug("API response: %s", json.dumps(response_json, indent=2))

                    return response_json
        except TimeoutError as err:
            raise SolisCloudControlApiError(f"Timeout accessing {url}") from err
        except aiohttp.ClientError as err:
            raise SolisCloudControlApiError(f"Error accessing {url}: {str(err)}") from err

    async def read(self, cid: int) -> str:
        payload = {"inverterSn": self._inverter_sn, "cid": cid}

        response_json = await self._request(READ_ENDPOINT, payload)

        code = response_json.get("code", "Unknown code")
        if str(code) != "0":
            error_msg = response_json.get("msg", "Unknown error")
            raise SolisCloudControlApiError(f"API operation failed: {error_msg}", response_code=code)

        if "data" not in response_json:
            raise SolisCloudControlApiError("API operation failed: 'data' field is missing in response")

        data = response_json["data"]

        if "msg" not in data:
            raise SolisCloudControlApiError("API operation failed: 'msg' field is missing in response")

        return data["msg"]

    async def control(self, cid: int, value: str) -> str:
        payload = {"inverterSn": self._inverter_sn, "cid": cid, "value": value}

        response_json = await self._request(CONTROL_ENDPOINT, payload)

        if "data" not in response_json:
            raise SolisCloudControlApiError("API operation failed: 'data' field is missing in response")

        data = response_json["data"][0]

        code = data.get("code", "Unknown code")
        if str(code) != "0":
            error_msg = data.get("msg", "Unknown error")
            raise SolisCloudControlApiError(f"API operation failed: {error_msg}", response_code=code)

        return value
