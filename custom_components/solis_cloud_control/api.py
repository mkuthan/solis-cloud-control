import base64
import hashlib
from datetime import datetime

# ...existing code...

VERB = "POST"
LOGIN_URL = "/v2/api/login"
CONTROL_URL = "/v2/api/control"
INVERTER_ID = "12345678"
# ...existing code...


class SolisCloudControlClient:
    def __init__(self, api_key: str, username: str, password: str):
        self.api_key = api_key
        self.username = username
        self.password = password
        self.base_url = "https://www.soliscloud.com:13333"


def digest(body: str) -> str:
    # ...existing code...
    return base64.b64encode(hashlib.md5(body.encode("utf-8")).digest()).decode("utf-8")


def passwordEncode(password: str) -> str:
    # ...existing code...
    return hashlib.md5(password.encode("utf-8")).hexdigest()


def prepare_header(
    config: dict[str, str], body: str, canonicalized_resource: str
) -> dict[str, str]:
    # ...existing code...
    # Uses digest, hmac, etc.
    # Return a dictionary of headers
    # ...existing code...
    return {
        # ...existing code...
    }


async def login(config):
    # ...existing code...
    # 1) build body, 2) prepare header, 3) do POST, 4) return csrfToken
    # ...existing code...
    return "token"


async def solis_control(config=None, days=None):
    # ...existing code...
    pass


def control_body(inverterId, chargeSettings) -> str:
    # ...existing code...
    return "{}"


def control_time_body(inverterId: str, currentTime: datetime) -> str:
    # ...existing code...
    return "{}"


async def set_control_times(token, inverterId: str, config, times):
    # ...existing code...
    pass


async def set_updated_time(token, inverterId: str, config, currentTime: datetime):
    # ...existing code...
    pass
