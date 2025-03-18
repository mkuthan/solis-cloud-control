from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    SolisCloudControlApiClientAuthenticationError,
    SolisCloudControlApiClientError,
)

from .data import SolisCloudControlConfigEntry


class SolisCloudControlDataUpdateCoordinator(DataUpdateCoordinator):
    config_entry: SolisCloudControlConfigEntry

    async def _async_update_data(self) -> any:
        try:
            return await self.config_entry.runtime_data.client.async_get_data()
        except SolisCloudControlApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except SolisCloudControlApiClientError as exception:
            raise UpdateFailed(exception) from exception
