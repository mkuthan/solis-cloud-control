from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers import device_registry as dr

from custom_components.solis_cloud_control.coordinator import SolisCloudControlCoordinator

from .api import SolisCloudControlApiClient
from .const import CONF_INVERTER_SN

PLATFORMS: list[Platform] = [Platform.SELECT, Platform.TEXT, Platform.NUMBER, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api_key = entry.data[CONF_API_KEY]
    api_token = entry.data[CONF_TOKEN]
    inverter_sn = entry.data[CONF_INVERTER_SN]

    session = aiohttp_client.async_get_clientsession(hass)
    api_client = SolisCloudControlApiClient(api_key, api_token, session)

    coordinator = SolisCloudControlCoordinator(hass, entry, api_client)
    entry.runtime_data = coordinator

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(entry.domain, inverter_sn)},
        manufacturer="Solis",
        name=f"Inverter {inverter_sn}",
    )

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
