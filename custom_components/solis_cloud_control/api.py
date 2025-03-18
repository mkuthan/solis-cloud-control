import base64
import hashlib
from datetime import datetime

BASE_URL = "https://www.soliscloud.com:13333"
VERB = "POST"
LOGIN_URL = "/v2/api/login"
CONTROL_URL = "/v2/api/control"
INVERTER_ID = "12345678"


class SolisCloudControlApiClientError(Exception):
    """Exception to indicate a general API error."""


class SolisCloudControlApiClientCommunicationError(
    SolisCloudControlApiClientError,
):
    """Exception to indicate a communication error."""


class SolisCloudControlApiClientAuthenticationError(
    SolisCloudControlApiClientError,
):
    """Exception to indicate an authentication error."""


class SolisCloudControlApiClient:
    def __init__(self, api_key: str, api_token: str, session):
        self.api_key = api_key
        self.api_token = api_token
        self.session = session

    async def validate(self):
        pass

    async def async_get_data(self):
        pass

    async def set_charge_discharge_schedule(self, call):
        pass


def digest(body: str) -> str:
    return base64.b64encode(hashlib.md5(body.encode("utf-8")).digest()).decode("utf-8")


def passwordEncode(password: str) -> str:
    return hashlib.md5(password.encode("utf-8")).hexdigest()


def prepare_header(
    config: dict[str, str], body: str, canonicalized_resource: str
) -> dict[str, str]:
    return {}


async def login(config):
    return "token"


async def solis_control(config=None, days=None):
    pass


def control_body(inverterId, chargeSettings) -> str:
    return "{}"


def control_time_body(inverterId: str, currentTime: datetime) -> str:
    return "{}"


async def set_control_times(token, inverterId: str, config, times):
    pass


async def set_updated_time(token, inverterId: str, config, currentTime: datetime):
    pass
