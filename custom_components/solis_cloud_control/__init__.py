from homeassistant.const import CONF_API_KEY, CONF_TOKEN
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.discovery import async_load_platform

from .api import SolisCloudControlApiClient, SolisCloudControlApiError
from .const import (
    CHARGE_SLOT1_CURRENT_CID,
    CHARGE_SLOT1_SOC_CID,
    CHARGE_SLOT1_TIME_CID,
    CONF_INVERTER_SN,
    CONTROL_SERVICE_NAME,
    CONTROL_SERVICE_SCHEMA,
    DISABLE_CHARGE_SLOT1_SERVICE_NAME,
    DISABLE_DISCHARGE_SLOT1_SERVICE_NAME,
    DISCHARGE_SLOT1_CURRENT_CID,
    DISCHARGE_SLOT1_SOC_CID,
    DISCHARGE_SLOT1_TIME_CID,
    DOMAIN,
    LOGGER,
    READ_SERVICE_NAME,
    READ_SERVICE_SCHEMA,
    SET_CHARGE_SLOT1_SERVICE_NAME,
    SET_CHARGE_SLOT1_SERVICE_SCHEMA,
    SET_DISCHARGE_SLOT1_SERVICE_NAME,
    SET_DISCHARGE_SLOT1_SERVICE_SCHEMA,
    SET_STORAGE_MODE_SERVICE_NAME,
    SET_STORAGE_MODE_SERVICE_SCHEMA,
    STORAGE_MODE_BIT_BACKUP_MODE,
    STORAGE_MODE_BIT_FEED_IN_PRIORITY,
    STORAGE_MODE_BIT_GRID_CHARGING,
    STORAGE_MODE_BIT_SELF_USE,
    STORAGE_MODE_CID,
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    conf = config.get(DOMAIN, {})

    api_key = conf.get(CONF_API_KEY)
    api_token = conf.get(CONF_TOKEN)
    inverter_sn = conf.get(CONF_INVERTER_SN)

    if not api_key:
        LOGGER.error("Missing required configuration entry: %s", CONF_API_KEY)
        return False
    if not api_token:
        LOGGER.error("Missing required configuration entry: %s", CONF_TOKEN)
        return False
    if not inverter_sn:
        LOGGER.error("Missing required configuration entry: %s", CONF_INVERTER_SN)
        return False

    session = aiohttp_client.async_get_clientsession(hass)

    client = SolisCloudControlApiClient(api_key, api_token, inverter_sn, session)

    hass.async_create_task(
        async_load_platform(
            hass,
            "select",
            DOMAIN,
            {"client": client, "inverter_sn": inverter_sn},
            config,
        )
    )

    async def async_service_read(call: ServiceCall) -> ServiceResponse:
        cid = call.data.get("cid")
        try:
            result = await client.read(cid)
            LOGGER.info("Read state for '%s': '%s'", cid, result)
            return {"value": result}
        except SolisCloudControlApiError as err:
            raise HomeAssistantError(str(err)) from err

    async def async_service_control(call: ServiceCall) -> None:
        cid = call.data.get("cid")
        value = call.data.get("value")
        try:
            LOGGER.info("Control '%s' state with value: '%s'", cid, value)
            await client.control(cid, value)
        except SolisCloudControlApiError as err:
            raise HomeAssistantError(str(err)) from err

    async def async_service_set_storage_mode(call: ServiceCall) -> ServiceResponse:
        storage_mode = call.data.get("storage_mode", "Self Use")
        battery_reserve = call.data.get("battery_reserve", "ON")
        allow_grid_charging = call.data.get("allow_grid_charging", "OFF")

        value_int = 0

        if storage_mode == "Self Use":
            value_int |= 1 << STORAGE_MODE_BIT_SELF_USE
        elif storage_mode == "Feed In Priority":
            value_int |= 1 << STORAGE_MODE_BIT_FEED_IN_PRIORITY

        if battery_reserve == "ON":
            value_int |= 1 << STORAGE_MODE_BIT_BACKUP_MODE

        if allow_grid_charging == "ON":
            value_int |= 1 << STORAGE_MODE_BIT_GRID_CHARGING

        value = str(value_int)

        try:
            LOGGER.info(
                "Setting storage mode: mode='%s', battery_reserve='%s', allow_grid_charging='%s', value='%s'",
                storage_mode,
                battery_reserve,
                allow_grid_charging,
                value,
            )
            await client.control(STORAGE_MODE_CID, value)
            return {"value": value}
        except SolisCloudControlApiError as err:
            raise HomeAssistantError(str(err)) from err

    async def async_service_set_charge_slot1(call: ServiceCall) -> ServiceResponse:
        from_time = call.data.get("from_time")
        to_time = call.data.get("to_time")
        current = call.data.get("current")
        soc = call.data.get("soc")

        from_time_formatted = from_time.strftime("%H:%M")
        to_time_formatted = to_time.strftime("%H:%M")

        time_range = f"{from_time_formatted}-{to_time_formatted}"
        response = {"time_range": time_range}

        try:
            LOGGER.info("Setting charge slot 1 time range: '%s'", time_range)
            await client.control(CHARGE_SLOT1_TIME_CID, time_range)

            if current is not None:
                current_str = str(current)
                LOGGER.info("Setting charge slot 1 current: '%s'", current_str)
                await client.control(CHARGE_SLOT1_CURRENT_CID, current_str)
                response["current"] = current

            if soc is not None:
                soc_str = str(soc)
                LOGGER.info("Setting charge slot 1 SOC: '%s'", soc_str)
                await client.control(CHARGE_SLOT1_SOC_CID, soc_str)
                response["soc"] = soc

            return response
        except SolisCloudControlApiError as err:
            raise HomeAssistantError(str(err)) from err

    async def async_service_set_discharge_slot1(call: ServiceCall) -> ServiceResponse:
        from_time = call.data.get("from_time")
        to_time = call.data.get("to_time")
        current = call.data.get("current")
        soc = call.data.get("soc")

        from_time_formatted = from_time.strftime("%H:%M")
        to_time_formatted = to_time.strftime("%H:%M")

        time_range = f"{from_time_formatted}-{to_time_formatted}"
        response = {"time_range": time_range}

        try:
            LOGGER.info("Setting discharge slot 1 time range: '%s'", time_range)
            await client.control(DISCHARGE_SLOT1_TIME_CID, time_range)

            if current is not None:
                current_str = str(current)
                LOGGER.info("Setting discharge slot 1 current: '%s'", current_str)
                await client.control(DISCHARGE_SLOT1_CURRENT_CID, current_str)
                response["current"] = current

            if soc is not None:
                soc_str = str(soc)
                LOGGER.info("Setting discharge slot 1 SOC: '%s'", soc_str)
                await client.control(DISCHARGE_SLOT1_SOC_CID, soc_str)
                response["soc"] = soc

            return response
        except SolisCloudControlApiError as err:
            raise HomeAssistantError(str(err)) from err

    async def async_service_disable_charge_slot1(call: ServiceCall) -> None:  # noqa: ARG001
        try:
            LOGGER.info("Disabling charge slot 1")
            await client.control(CHARGE_SLOT1_TIME_CID, "00:00-00:00")
        except SolisCloudControlApiError as err:
            raise HomeAssistantError(str(err)) from err

    async def async_service_disable_discharge_slot1(call: ServiceCall) -> None:  # noqa: ARG001
        try:
            LOGGER.info("Disabling discharge slot 1")
            await client.control(DISCHARGE_SLOT1_TIME_CID, "00:00-00:00")
        except SolisCloudControlApiError as err:
            raise HomeAssistantError(str(err)) from err

    hass.services.async_register(
        DOMAIN,
        READ_SERVICE_NAME,
        async_service_read,
        supports_response=SupportsResponse.ONLY,
        schema=READ_SERVICE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        CONTROL_SERVICE_NAME,
        async_service_control,
        supports_response=SupportsResponse.NONE,
        schema=CONTROL_SERVICE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SET_STORAGE_MODE_SERVICE_NAME,
        async_service_set_storage_mode,
        supports_response=SupportsResponse.ONLY,
        schema=SET_STORAGE_MODE_SERVICE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SET_CHARGE_SLOT1_SERVICE_NAME,
        async_service_set_charge_slot1,
        supports_response=SupportsResponse.ONLY,
        schema=SET_CHARGE_SLOT1_SERVICE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SET_DISCHARGE_SLOT1_SERVICE_NAME,
        async_service_set_discharge_slot1,
        supports_response=SupportsResponse.ONLY,
        schema=SET_DISCHARGE_SLOT1_SERVICE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        DISABLE_CHARGE_SLOT1_SERVICE_NAME,
        async_service_disable_charge_slot1,
        supports_response=SupportsResponse.NONE,
    )
    hass.services.async_register(
        DOMAIN,
        DISABLE_DISCHARGE_SLOT1_SERVICE_NAME,
        async_service_disable_discharge_slot1,
        supports_response=SupportsResponse.NONE,
    )

    return True
