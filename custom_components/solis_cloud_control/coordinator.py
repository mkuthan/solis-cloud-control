import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.solis_cloud_control.api import SolisCloudControlApiClient, SolisCloudControlApiError
from custom_components.solis_cloud_control.const import (
    CID_BATTERY_FORCE_CHARGE_SOC,
    CID_BATTERY_OVER_DISCHARGE_SOC,
    CID_BATTERY_RECOVERY_SOC,
    CID_BATTERY_RESERVE_SOC,
    CID_CHARGE_SLOT1_CURRENT,
    CID_CHARGE_SLOT1_SOC,
    CID_CHARGE_SLOT1_SWITCH,
    CID_CHARGE_SLOT1_TIME,
    CID_CHARGE_SLOT2_SWITCH,
    CID_CHARGE_SLOT3_SWITCH,
    CID_CHARGE_SLOT4_SWITCH,
    CID_CHARGE_SLOT5_SWITCH,
    CID_CHARGE_SLOT6_SWITCH,
    CID_DISCHARGE_SLOT1_CURRENT,
    CID_DISCHARGE_SLOT1_SOC,
    CID_DISCHARGE_SLOT1_SWITCH,
    CID_DISCHARGE_SLOT1_TIME,
    CID_DISCHARGE_SLOT2_SWITCH,
    CID_DISCHARGE_SLOT3_SWITCH,
    CID_DISCHARGE_SLOT4_SWITCH,
    CID_DISCHARGE_SLOT5_SWITCH,
    CID_DISCHARGE_SLOT6_SWITCH,
    CID_MAX_EXPORT_POWER,
    CID_STORAGE_MODE,
    CONF_INVERTER_SN,
)

_LOGGER = logging.getLogger(__name__)

_NAME = "Solis Cloud Control"

_UPDATE_INTERVAL = timedelta(minutes=3)

_CONTROL_RETRY_COUNT = 1  # initial attempt + 1 retry
_CONTROL_RETRY_DELAY_SECONDS = 5

_ALL_CIDS = [
    CID_BATTERY_FORCE_CHARGE_SOC,
    CID_BATTERY_OVER_DISCHARGE_SOC,
    CID_BATTERY_RECOVERY_SOC,
    CID_BATTERY_RESERVE_SOC,
    CID_CHARGE_SLOT1_CURRENT,
    CID_CHARGE_SLOT1_SOC,
    CID_CHARGE_SLOT1_SWITCH,
    CID_CHARGE_SLOT1_TIME,
    CID_CHARGE_SLOT2_SWITCH,
    CID_CHARGE_SLOT3_SWITCH,
    CID_CHARGE_SLOT4_SWITCH,
    CID_CHARGE_SLOT5_SWITCH,
    CID_CHARGE_SLOT6_SWITCH,
    CID_DISCHARGE_SLOT1_CURRENT,
    CID_DISCHARGE_SLOT1_SOC,
    CID_DISCHARGE_SLOT1_SWITCH,
    CID_DISCHARGE_SLOT1_TIME,
    CID_DISCHARGE_SLOT2_SWITCH,
    CID_DISCHARGE_SLOT3_SWITCH,
    CID_DISCHARGE_SLOT4_SWITCH,
    CID_DISCHARGE_SLOT5_SWITCH,
    CID_DISCHARGE_SLOT6_SWITCH,
    CID_MAX_EXPORT_POWER,
    CID_STORAGE_MODE,
]


class SolisCloudControlData(dict[int, str | None]):
    pass


class SolisCloudControlCoordinator(DataUpdateCoordinator[SolisCloudControlData]):
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api_client: SolisCloudControlApiClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=_NAME,
            config_entry=config_entry,
            update_interval=_UPDATE_INTERVAL,
        )
        self._api_client = api_client
        self._inverter_sn = config_entry.data[CONF_INVERTER_SN]

    async def _async_update_data(self) -> SolisCloudControlData:
        try:
            result = await self._api_client.read_batch(self._inverter_sn, _ALL_CIDS)
            data = SolisCloudControlData({cid: result.get(cid) for cid in _ALL_CIDS})
            _LOGGER.debug("Data read from API: %s", data)
            return data
        except SolisCloudControlApiError as error:
            raise UpdateFailed(error) from error

    async def control(
        self,
        cid: int,
        value: str,
        old_value: str | None = None,
        retry_count: int = _CONTROL_RETRY_COUNT,
        retry_delay: float = _CONTROL_RETRY_DELAY_SECONDS,
    ) -> None:
        attempt = 0

        while attempt <= retry_count:
            await self._api_client.control(self._inverter_sn, cid, value, old_value)
            current_value = await self._api_client.read(self._inverter_sn, cid)

            if current_value == value:
                await self.async_request_refresh()
                return

            attempt += 1
            if attempt <= retry_count:
                _LOGGER.warning(
                    "Retrying due to verification failed, current value: %s (attempt %d/%d)",
                    current_value,
                    attempt,
                    retry_count,
                )
                await asyncio.sleep(retry_delay)
            else:
                raise HomeAssistantError(
                    f"Failed to set value for CID {cid}. " f"Expected: {value}, got: {current_value}"
                )
