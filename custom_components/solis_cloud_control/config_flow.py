import voluptuous as vol
from homeassistant import config_entries

from . import DOMAIN


class SolisCloudControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Solis Cloud Control", data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                    vol.Required("key_id"): str,
                    vol.Required("secret"): str,
                }
            ),
        )
