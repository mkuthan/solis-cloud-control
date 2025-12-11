import logging

from homeassistant.const import CONF_API_KEY, CONF_API_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers import device_registry as dr

from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient
from custom_components.solis_cloud_control.const import API_BASE_URL, CONF_INVERTER_SN
from custom_components.solis_cloud_control.coordinator import SolisCloudControlCoordinator
from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry, SolisCloudControlData
from custom_components.solis_cloud_control.inverters.inverter_factory import create_inverter, create_inverter_info

_LOGGER = logging.getLogger(__name__)

_PLATFORMS: list[Platform] = [
    Platform.DATETIME,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TEXT,
]


async def async_setup_entry(hass: HomeAssistant, config_entry: SolisCloudControlConfigEntry) -> bool:
    api_key = config_entry.data[CONF_API_KEY]
    api_token = config_entry.data[CONF_API_TOKEN]
    inverter_sn = config_entry.data[CONF_INVERTER_SN]

    # create api client
    api_client = _create_api_client(hass, api_key, api_token)

    # create inverter
    inverter_info = await create_inverter_info(api_client, inverter_sn)
    inverter = create_inverter(inverter_info)

    # register the inverter in the device registry
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(config_entry.domain, inverter_sn)},
        manufacturer="Solis",
        name=f"Inverter Control {inverter_sn}",
        serial_number=inverter_sn,
        model_id=inverter_info.model or "Unknown",
        model=inverter_info.machine or "Unknown",
        sw_version=inverter_info.version or "Unknown",
    )

    # create coordinator
    coordinator = SolisCloudControlCoordinator(hass, config_entry, api_client, inverter)

    # perform an initial data load from api
    await coordinator.async_config_entry_first_refresh()

    # make coordinator available to integration
    config_entry.runtime_data = SolisCloudControlData(inverter, coordinator)

    # setup platforms, call async_setup for each entity
    await hass.config_entries.async_forward_entry_setups(config_entry, _PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: SolisCloudControlConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(config_entry, _PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, config_entry: SolisCloudControlConfigEntry) -> bool:
    _LOGGER.debug("Migrating configuration from version %s", config_entry.version)

    new_data = {**config_entry.data}

    if config_entry.version == 1:
        from homeassistant.const import CONF_TOKEN

        new_data[CONF_API_TOKEN] = new_data.pop(CONF_TOKEN)

    hass.config_entries.async_update_entry(config_entry, data=new_data, version=2)

    return True


def _create_api_client(hass: HomeAssistant, api_key: str, api_token: str) -> SolisCloudControlApiClient:
    session = aiohttp_client.async_get_clientsession(hass)
    return SolisCloudControlApiClient(API_BASE_URL, api_key, api_token, session)
