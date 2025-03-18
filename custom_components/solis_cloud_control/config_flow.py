from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_API_TOKEN
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from slugify import slugify

from .api import (
    SolisCloudControlApiClient,
    SolisCloudControlApiClientAuthenticationError,
    SolisCloudControlApiClientCommunicationError,
    SolisCloudControlApiClientError,
)
from .const import DOMAIN, LOGGER


class SolisCloudControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        _errors = {}
        if user_input is not None:
            try:
                await self._test_credentials(
                    api_key=user_input[CONF_API_KEY],
                    api_token=user_input[CONF_API_TOKEN],
                )
            except SolisCloudControlApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except SolisCloudControlApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except SolisCloudControlApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(slugify(user_input[CONF_API_KEY]))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_API_KEY],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                    vol.Required(CONF_API_TOKEN): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        ),
                    ),
                }
            ),
            errors=_errors,
        )

    async def _test_credentials(self, api_key: str, api_token: str) -> None:
        client = SolisCloudControlApiClient(
            api_key=api_key,
            api_token=api_token,
            session=async_create_clientsession(self.hass),
        )
        await client.async_validate()
