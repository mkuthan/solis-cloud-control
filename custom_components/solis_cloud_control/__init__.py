from homeassistant.const import CONF_API_KEY, CONF_TOKEN
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse
from homeassistant.helpers import aiohttp_client

from .api import SolisCloudControlApiClient, SolisCloudControlApiError
from .const import DOMAIN, LOGGER


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    conf = config.get(DOMAIN, {})

    api_key = conf.get(CONF_API_KEY)
    api_token = conf.get(CONF_TOKEN)
    inverter_sn = conf.get("inverter_sn")

    session = aiohttp_client.async_get_clientsession(hass)

    client = SolisCloudControlApiClient(api_key, api_token, inverter_sn, session)

    async def async_service_read(call: ServiceCall) -> ServiceResponse:
        cid = call.data.get("cid")
        try:
            result = await client.read(cid)
            LOGGER.info("Read result: %s", result)
            return {"success": True, "result": result}
        except SolisCloudControlApiError as err:
            LOGGER.error("Read action failed: %s", err)
            return {"success": False, "error": str(err)}

    async def async_service_control(call: ServiceCall) -> ServiceResponse:
        cid = call.data.get("cid")
        value = call.data.get("value")
        try:
            result = await client.control(cid, value)
            LOGGER.info("Control result: %s", result)
            return {"success": True, "result": result}
        except SolisCloudControlApiError as err:
            LOGGER.error("Control action failed: %s", err)
            return {"success": False, "error": str(err)}

    hass.services.async_register(DOMAIN, "read", async_service_read)
    hass.services.async_register(DOMAIN, "control", async_service_control)

    return True
