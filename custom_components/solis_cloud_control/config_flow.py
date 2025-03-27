import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY, CONF_TOKEN
from homeassistant.helpers import aiohttp_client

from custom_components.solis_cloud_control.api import SolisCloudControlApiClient, SolisCloudControlApiError

from .const import CID_STORAGE_MODE, CONF_INVERTER_SN, DOMAIN

_LOGGER = logging.getLogger(__name__)

_STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_TOKEN): str,
        vol.Required(CONF_INVERTER_SN): str,
    }
)


class SolisCloudControlFlowHandler(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await self._test_credentials(
                    api_key=user_input[CONF_API_KEY],
                    api_token=user_input[CONF_TOKEN],
                    inverter_sn=user_input[CONF_INVERTER_SN],
                )
            except SolisCloudControlApiError as error:
                if error.response_code == "Z0001":
                    errors["base"] = "invalid_auth"
                elif error.response_code == "B0124":
                    errors["base"] = "invalid_inverter_sn"
                else:
                    errors["base"] = "connection_error"
            except Exception as error:
                _LOGGER.exception(error)
                errors["base"] = "unknown_error"
            else:
                await self.async_set_unique_id(unique_id=user_input[CONF_INVERTER_SN])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_API_KEY],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def _test_credentials(self, api_key: str, api_token: str, inverter_sn: str) -> None:
        session = aiohttp_client.async_get_clientsession(self.hass)
        api_client = SolisCloudControlApiClient(api_key, api_token, session)
        await api_client.read(inverter_sn, CID_STORAGE_MODE)
