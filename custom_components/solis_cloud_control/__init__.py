from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.solis_cloud_control.api import SolisCloudControlClient


DOMAIN = "solis_cloud_control"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data[DOMAIN] = SolisCloudControlClient(
        entry.data["api_key"], entry.data["username"], entry.data["password"]
    )

    hass.services.async_register(
        DOMAIN, "set_inverter_mode", hass.data[DOMAIN].set_inverter_mode
    )
    hass.services.async_register(
        DOMAIN,
        "set_charge_discharge_schedule",
        hass.data[DOMAIN].set_charge_discharge_schedule,
    )

    return True
