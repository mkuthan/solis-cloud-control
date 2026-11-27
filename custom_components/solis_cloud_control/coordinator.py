import logging
from dataclasses import dataclass, field
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.solis_cloud_control.services.cid_service import CidServiceError

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from custom_components.solis_cloud_control.domain.remote_dispatch import RemoteDispatch
    from custom_components.solis_cloud_control.services.cid_service import CidService

_LOGGER = logging.getLogger(__name__)

_COORDINATOR_NAME = "Solis Cloud Control"

_UPDATE_INTERVAL = timedelta(minutes=5)

_REQUEST_REFRESH_COOLDOWN_SECONDS = 10


@dataclass
class SolisCloudControlData:
    cids: dict[int, str | None] = field(default_factory=dict)
    remote_dispatch: RemoteDispatch | None = None


class SolisCloudControlCoordinator(DataUpdateCoordinator[SolisCloudControlData]):
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        cid_service: CidService,
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
        self._cid_service = cid_service

    async def _async_update_data(self) -> SolisCloudControlData:
        try:
            cids = await self._cid_service.read_all()
            data = SolisCloudControlData(cids=cids)
            _LOGGER.debug("Data read from API: %s", data)
            return data
        except CidServiceError as error:
            raise UpdateFailed(error) from error

    async def control(
        self,
        cid: int,
        value: str,
        old_value: str | None = None,
    ) -> None:
        if self.data:
            cids = {**self.data.cids, cid: value}
            new_data = SolisCloudControlData(cids=cids, remote_dispatch=self.data.remote_dispatch)
            self.async_set_updated_data(new_data)

        try:
            await self._cid_service.control(cid, value, old_value)
        finally:
            await self.async_request_refresh()
