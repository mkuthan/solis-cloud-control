from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "solis_cloud_control"

API_BASE_URL = "https://www.soliscloud.com:13333"
API_TIMEOUT_SECONDS = 10
READ_ENDPOINT = "/v2/api/atRead"
CONTROL_ENDPOINT = "/v2/api/control"
