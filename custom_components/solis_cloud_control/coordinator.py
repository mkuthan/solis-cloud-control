import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient, SolisCloudControlApiError
from custom_components.solis_cloud_control.inverters.inverter import Inverter

_LOGGER = logging.getLogger(__name__)

_COORDINATOR_NAME = "Solis Cloud Control"

_UPDATE_INTERVAL = timedelta(minutes=5)

_REQUEST_REFRESH_COOLDOWN_SECONDS = 10

_UPDATE_BATCH_DATA_MAX_RETRY_TIME_SECONDS = 180
_UPDATE_DATA_MAX_RETRY_TIME_SECONDS = 60


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
            request_refresh_debouncer=Debouncer(
                hass,
                _LOGGER,
                cooldown=_REQUEST_REFRESH_COOLDOWN_SECONDS,
                immediate=False,
            ),
        )
        self._api_client = api_client
        self._inverter = inverter

    async def _async_update_data(self) -> SolisCloudControlData:
        inverter_sn = self._inverter.info.serial_number
        try:
            results = await self._api_client.read_batch(
                inverter_sn,
                self._inverter.read_batch_cids,
                max_retry_time=_UPDATE_BATCH_DATA_MAX_RETRY_TIME_SECONDS,
            )

            for read_cid in self._inverter.read_cids:
                results[read_cid] = await self._api_client.read(
                    inverter_sn,
                    read_cid,
                    max_retry_time=_UPDATE_DATA_MAX_RETRY_TIME_SECONDS,
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
    ) -> None:
        if self.data:
            new_data = SolisCloudControlData(self.data)
            new_data[cid] = value
            self.async_set_updated_data(new_data)

        try:
            inverter_sn = self._inverter.info.serial_number
            await self._api_client.control(inverter_sn, cid, value, old_value)
        finally:
            await self.async_request_refresh()
