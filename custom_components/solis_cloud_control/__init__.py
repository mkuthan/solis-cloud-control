from datetime import timedelta

from homeassistant.const import CONF_API_KEY, CONF_API_TOKEN, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration
from homeassistant.core import HomeAssistant


from .api import SolisCloudControlApiClient
from .const import DOMAIN, LOGGER
from .coordinator import SolisCloudControlDataUpdateCoordinator
from .data import SolisCloudControlData, SolisCloudControlConfigEntry


PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SolisCloudControlConfigEntry,
) -> bool:
    coordinator = SolisCloudControlDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(hours=1),
    )
    entry.runtime_data = SolisCloudControlData(
        client=SolisCloudControlApiClient(
            api_key=entry.data[CONF_API_KEY],
            api_token=entry.data[CONF_API_TOKEN],
            session=async_get_clientsession(hass),
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: SolisCloudControlConfigEntry,
) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: SolisCloudControlConfigEntry,
) -> None:
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
