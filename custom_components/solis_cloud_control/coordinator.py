import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.solis_cloud_control.api import SolisCloudControlApiClient, SolisCloudControlApiError
from custom_components.solis_cloud_control.const import (
    CID_CHARGE_SLOT1_CURRENT,
    CID_CHARGE_SLOT1_SOC,
    CID_CHARGE_SLOT1_TIME,
    CID_DISCHARGE_SLOT1_CURRENT,
    CID_DISCHARGE_SLOT1_SOC,
    CID_DISCHARGE_SLOT1_TIME,
    CID_STORAGE_MODE,
)

_LOGGER = logging.getLogger(__name__)

_ALL_CIDS = [
    CID_STORAGE_MODE,
    CID_CHARGE_SLOT1_CURRENT,
    CID_CHARGE_SLOT1_SOC,
    CID_CHARGE_SLOT1_TIME,
    CID_DISCHARGE_SLOT1_CURRENT,
    CID_DISCHARGE_SLOT1_SOC,
    CID_DISCHARGE_SLOT1_TIME,
]


class SolisCloudControlData(dict[int, str | None]):
    pass


type SolisCloudControlConfigEntry = ConfigEntry[SolisCloudControlData]


class SolisCloudControlCoordinator(DataUpdateCoordinator[SolisCloudControlData]):
    config_entry: SolisCloudControlConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: SolisCloudControlConfigEntry, api_client: SolisCloudControlApiClient
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Solis Cloud Control Coordinator",
            config_entry=config_entry,
            update_interval=timedelta(minutes=5),
        )
        self.api_client = api_client

    async def _async_update_data(self) -> SolisCloudControlData:
        try:
            result = await self.api_client.read_batch(_ALL_CIDS)
            data = SolisCloudControlData({cid: result.get(cid) for cid in _ALL_CIDS})
            _LOGGER.debug("Data read from API: %s", data)
            return data
        except SolisCloudControlApiError as error:
            raise UpdateFailed(error) from error
