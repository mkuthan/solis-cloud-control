import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY, CONF_API_TOKEN
from homeassistant.helpers import aiohttp_client

from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient, SolisCloudControlApiError
from custom_components.solis_cloud_control.const import API_BASE_URL, CONF_INVERTER_SN, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SolisCloudControlFlowHandler(ConfigFlow, domain=DOMAIN):
    VERSION = 2

    def __init__(self) -> None:
        self._api_key: str | None = None
        self._api_token: str | None = None
        self._inverter_options: dict[str, str] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                self._api_key = user_input[CONF_API_KEY]
                self._api_token = user_input[CONF_API_TOKEN]

                inverters = await self._inverter_list()

                for inverter in inverters:
                    if "sn" not in inverter:
                        _LOGGER.warning("Inverter does not have a serial number 'sn' field, skipping")
                        continue
                    inverter_sn = inverter["sn"]
                    station_name = inverter.get("stationName", "Unknown Station")
                    self._inverter_options[inverter_sn] = f"{inverter_sn} ({station_name})"

                if not self._inverter_options:
                    errors["base"] = "no_inverters"
                else:
                    return await self.async_step_select_inverter()

            except SolisCloudControlApiError as error:
                _LOGGER.warning(error, exc_info=True)
                if error.response_code == "Z0001":
                    errors["base"] = "invalid_auth"
                else:
                    errors["base"] = "cannot_connect"
            except Exception as error:
                _LOGGER.warning(error, exc_info=True)
                errors["base"] = "unknown"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_API_TOKEN): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_select_inverter(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_INVERTER_SN])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Inverter {user_input[CONF_INVERTER_SN]}",
                data={
                    CONF_API_KEY: self._api_key,
                    CONF_API_TOKEN: self._api_token,
                    CONF_INVERTER_SN: user_input[CONF_INVERTER_SN],
                },
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_INVERTER_SN): vol.In(self._inverter_options),
            }
        )

        return self.async_show_form(
            step_id="select_inverter",
            data_schema=data_schema,
            errors=errors,
        )

    async def _inverter_list(self) -> list[dict[str, Any]]:
        api_client = SolisCloudControlApiClient(
            API_BASE_URL, self._api_key, self._api_token, aiohttp_client.async_get_clientsession(self.hass)
        )
        return await api_client.inverter_list(max_retry_time=0.0)
