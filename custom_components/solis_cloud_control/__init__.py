from homeassistant.const import CONF_API_KEY, CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from custom_components.solis_cloud_control.coordinator import SolisCloudControlConfigEntry, SolisCloudControlCoordinator

from .api import SolisCloudControlApiClient
from .const import CONF_INVERTER_SN

PLATFORMS: list[Platform] = [Platform.SELECT]


async def async_setup_entry(hass: HomeAssistant, entry: SolisCloudControlConfigEntry) -> bool:
    api_key = entry.data[CONF_API_KEY]
    api_token = entry.data[CONF_TOKEN]
    inverter_sn = entry.data[CONF_INVERTER_SN]

    session = aiohttp_client.async_get_clientsession(hass)
    api_client = SolisCloudControlApiClient(api_key, api_token, inverter_sn, session)

    coordinator = SolisCloudControlCoordinator(
        hass,
        entry,
        api_client,
    )

    entry.runtime_data = coordinator

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # hass.async_create_task(
    #     async_load_platform(
    #         hass,
    #         "select",
    #         DOMAIN,
    #         {"client": api_client, "inverter_sn": inverter_sn},
    #         entry,
    #     )
    # )

    # async def async_service_read(call: ServiceCall) -> ServiceResponse:
    #     cid = call.data.get("cid")
    #     try:
    #         result = await api_client.read(cid)
    #         _LOGGER.info("Read state for '%s': '%s'", cid, result)
    #         return {"value": result}
    #     except SolisCloudControlApiError as err:
    #         raise HomeAssistantError(str(err)) from err

    # async def async_service_control(call: ServiceCall) -> None:
    #     cid = call.data.get("cid")
    #     value = call.data.get("value")
    #     try:
    #         _LOGGER.info("Control '%s' state with value: '%s'", cid, value)
    #         await api_client.control(cid, value)
    #     except SolisCloudControlApiError as err:
    #         raise HomeAssistantError(str(err)) from err

    # async def async_service_set_storage_mode(call: ServiceCall) -> ServiceResponse:
    #     storage_mode = call.data.get("storage_mode", "Self Use")
    #     battery_reserve = call.data.get("battery_reserve", "ON")
    #     allow_grid_charging = call.data.get("allow_grid_charging", "OFF")

    #     value_int = 0

    #     if storage_mode == "Self Use":
    #         value_int |= 1 << STORAGE_MODE_BIT_SELF_USE
    #     elif storage_mode == "Feed In Priority":
    #         value_int |= 1 << STORAGE_MODE_BIT_FEED_IN_PRIORITY

    #     if battery_reserve == "ON":
    #         value_int |= 1 << STORAGE_MODE_BIT_BACKUP_MODE

    #     if allow_grid_charging == "ON":
    #         value_int |= 1 << STORAGE_MODE_BIT_GRID_CHARGING

    #     value = str(value_int)

    #     try:
    #         _LOGGER.info(
    #             "Setting storage mode: mode='%s', battery_reserve='%s', allow_grid_charging='%s', value='%s'",
    #             storage_mode,
    #             battery_reserve,
    #             allow_grid_charging,
    #             value,
    #         )
    #         await api_client.control(STORAGE_MODE_CID, value)
    #         return {"value": value}
    #     except SolisCloudControlApiError as err:
    #         raise HomeAssistantError(str(err)) from err

    # async def async_service_set_charge_slot1(call: ServiceCall) -> ServiceResponse:
    #     from_time = call.data.get("from_time")
    #     to_time = call.data.get("to_time")
    #     current = call.data.get("current")
    #     soc = call.data.get("soc")

    #     from_time_formatted = from_time.strftime("%H:%M")
    #     to_time_formatted = to_time.strftime("%H:%M")

    #     time_range = f"{from_time_formatted}-{to_time_formatted}"
    #     response = {"time_range": time_range}

    #     try:
    #         _LOGGER.info("Setting charge slot 1 time range: '%s'", time_range)
    #         await api_client.control(CHARGE_SLOT1_TIME_CID, time_range)

    #         if current is not None:
    #             current_str = str(current)
    #             _LOGGER.info("Setting charge slot 1 current: '%s'", current_str)
    #             await api_client.control(CHARGE_SLOT1_CURRENT_CID, current_str)
    #             response["current"] = current

    #         if soc is not None:
    #             soc_str = str(soc)
    #             _LOGGER.info("Setting charge slot 1 SOC: '%s'", soc_str)
    #             await api_client.control(CHARGE_SLOT1_SOC_CID, soc_str)
    #             response["soc"] = soc

    #         return response
    #     except SolisCloudControlApiError as err:
    #         raise HomeAssistantError(str(err)) from err

    # async def async_service_set_discharge_slot1(call: ServiceCall) -> ServiceResponse:
    #     from_time = call.data.get("from_time")
    #     to_time = call.data.get("to_time")
    #     current = call.data.get("current")
    #     soc = call.data.get("soc")

    #     from_time_formatted = from_time.strftime("%H:%M")
    #     to_time_formatted = to_time.strftime("%H:%M")

    #     time_range = f"{from_time_formatted}-{to_time_formatted}"
    #     response = {"time_range": time_range}

    #     try:
    #         _LOGGER.info("Setting discharge slot 1 time range: '%s'", time_range)
    #         await api_client.control(DISCHARGE_SLOT1_TIME_CID, time_range)

    #         if current is not None:
    #             current_str = str(current)
    #             _LOGGER.info("Setting discharge slot 1 current: '%s'", current_str)
    #             await api_client.control(DISCHARGE_SLOT1_CURRENT_CID, current_str)
    #             response["current"] = current

    #         if soc is not None:
    #             soc_str = str(soc)
    #             _LOGGER.info("Setting discharge slot 1 SOC: '%s'", soc_str)
    #             await api_client.control(DISCHARGE_SLOT1_SOC_CID, soc_str)
    #             response["soc"] = soc

    #         return response
    #     except SolisCloudControlApiError as err:
    #         raise HomeAssistantError(str(err)) from err

    # async def async_service_disable_charge_slot1(call: ServiceCall) -> None:  # noqa: ARG001
    #     try:
    #         _LOGGER.info("Disabling charge slot 1")
    #         await api_client.control(CHARGE_SLOT1_TIME_CID, "00:00-00:00")
    #     except SolisCloudControlApiError as err:
    #         raise HomeAssistantError(str(err)) from err

    # async def async_service_disable_discharge_slot1(call: ServiceCall) -> None:  # noqa: ARG001
    #     try:
    #         _LOGGER.info("Disabling discharge slot 1")
    #         await api_client.control(DISCHARGE_SLOT1_TIME_CID, "00:00-00:00")
    #     except SolisCloudControlApiError as err:
    #         raise HomeAssistantError(str(err)) from err

    # hass.services.async_register(
    #     DOMAIN,
    #     READ_SERVICE_NAME,
    #     async_service_read,
    #     supports_response=SupportsResponse.ONLY,
    #     schema=READ_SERVICE_SCHEMA,
    # )
    # hass.services.async_register(
    #     DOMAIN,
    #     CONTROL_SERVICE_NAME,
    #     async_service_control,
    #     supports_response=SupportsResponse.NONE,
    #     schema=CONTROL_SERVICE_SCHEMA,
    # )
    # hass.services.async_register(
    #     DOMAIN,
    #     SET_STORAGE_MODE_SERVICE_NAME,
    #     async_service_set_storage_mode,
    #     supports_response=SupportsResponse.ONLY,
    #     schema=SET_STORAGE_MODE_SERVICE_SCHEMA,
    # )
    # hass.services.async_register(
    #     DOMAIN,
    #     SET_CHARGE_SLOT1_SERVICE_NAME,
    #     async_service_set_charge_slot1,
    #     supports_response=SupportsResponse.ONLY,
    #     schema=SET_CHARGE_SLOT1_SERVICE_SCHEMA,
    # )
    # hass.services.async_register(
    #     DOMAIN,
    #     SET_DISCHARGE_SLOT1_SERVICE_NAME,
    #     async_service_set_discharge_slot1,
    #     supports_response=SupportsResponse.ONLY,
    #     schema=SET_DISCHARGE_SLOT1_SERVICE_SCHEMA,
    # )
    # hass.services.async_register(
    #     DOMAIN,
    #     DISABLE_CHARGE_SLOT1_SERVICE_NAME,
    #     async_service_disable_charge_slot1,
    #     supports_response=SupportsResponse.NONE,
    # )
    # hass.services.async_register(
    #     DOMAIN,
    #     DISABLE_DISCHARGE_SLOT1_SERVICE_NAME,
    #     async_service_disable_discharge_slot1,
    #     supports_response=SupportsResponse.NONE,
    # )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: SolisCloudControlConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
