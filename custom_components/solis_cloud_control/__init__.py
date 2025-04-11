import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_API_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers import device_registry as dr

from custom_components.solis_cloud_control.coordinator import SolisCloudControlCoordinator

from .api import SolisCloudControlApiClient
from .const import API_BASE_URL, CONF_INVERTER_SN

_LOGGER = logging.getLogger(__name__)

_PLATFORMS: list[Platform] = [Platform.SELECT, Platform.TEXT, Platform.NUMBER, Platform.SWITCH, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api_key = entry.data[CONF_API_KEY]
    api_token = entry.data[CONF_API_TOKEN]
    inverter_sn = entry.data[CONF_INVERTER_SN]

    session = aiohttp_client.async_get_clientsession(hass)
    api_client = SolisCloudControlApiClient(API_BASE_URL, api_key, api_token, session)

    coordinator = SolisCloudControlCoordinator(hass, entry, api_client)
    entry.runtime_data = coordinator

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(entry.domain, inverter_sn)},
        manufacturer="Solis",
        name=f"Inverter Control {inverter_sn}",
    )

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    _LOGGER.debug("Migrating configuration from version %s", config_entry.version)

    new_data = {**config_entry.data}

    if config_entry.version == 1:
        from homeassistant.const import CONF_TOKEN

        new_data[CONF_API_TOKEN] = new_data.pop(CONF_TOKEN)

    hass.config_entries.async_update_entry(config_entry, data=new_data, version=2)

    return True
