import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient, SolisCloudControlApiError
from custom_components.solis_cloud_control.inverters.inverter import Inverter

_LOGGER = logging.getLogger(__name__)

_COORDINATOR_NAME = "Solis Cloud Control"

_UPDATE_INTERVAL = timedelta(minutes=3)


_UPDATE_DATA_RETRY_COUNT = 5  # initial attempt + 5 retries
_UPDATE_DATA_RETRY_DELAY_SECONDS = 10
_CONTROL_RETRY_COUNT = 1  # initial attempt + 1 retry
_CONTROL_RETRY_DELAY_SECONDS = 5


class SolisCloudControlData(dict[int, str | None]):
    pass


class SolisCloudControlCoordinator(DataUpdateCoordinator[SolisCloudControlData]):
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api_client: SolisCloudControlApiClient,
        inverter: Inverter,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=_COORDINATOR_NAME,
            config_entry=config_entry,
            update_interval=_UPDATE_INTERVAL,
        )
        self._api_client = api_client
        self._inverter = inverter

    async def _async_update_data(self) -> SolisCloudControlData:
        inverter_sn = self._inverter.info.serial_number
        try:
            results = await self._api_client.read_batch(
                inverter_sn,
                self._inverter.read_batch_cids,
                retry_count=_UPDATE_DATA_RETRY_COUNT,
                retry_delay=_UPDATE_DATA_RETRY_DELAY_SECONDS,
            )

            for read_cid in self._inverter.read_cids:
                results[read_cid] = await self._api_client.read(
                    inverter_sn,
                    read_cid,
                    retry_count=_UPDATE_DATA_RETRY_COUNT,
                    retry_delay=_UPDATE_DATA_RETRY_DELAY_SECONDS,
                )

            data = SolisCloudControlData({cid: results.get(cid) for cid in self._inverter.all_cids})
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
        inverter_sn = self._inverter.info.serial_number

        attempt = 0

        while attempt <= retry_count:
            await self._api_client.control(inverter_sn, cid, value, old_value)

            current_value = await self._api_client.read(inverter_sn, cid)
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
                raise HomeAssistantError(f"Failed to set value for CID {cid}. Expected: {value}, got: {current_value}")

    async def control_no_check(
        self,
        cid: int,
        value: str,
        old_value: str | None = None,
    ) -> None:
        inverter_sn = self._inverter.info.serial_number
        await self._api_client.control(inverter_sn, cid, value, old_value)
        await self.async_request_refresh()
