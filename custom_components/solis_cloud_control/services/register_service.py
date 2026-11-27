from typing import TYPE_CHECKING

from custom_components.solis_cloud_control.api.solis_api_error import SolisCloudControlApiError
from custom_components.solis_cloud_control.domain.remote_dispatch import HOLDING_COUNT, HOLDING_START
from custom_components.solis_cloud_control.utils.modbus import build_write_registers_frame, to_u16

if TYPE_CHECKING:
    from collections.abc import Sequence

    from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient
    from custom_components.solis_cloud_control.domain.remote_dispatch import RegisterWrite
    from custom_components.solis_cloud_control.inverters.inverter import Inverter


class RegisterServiceError(Exception):
    pass


class RegisterService:
    _HOLDING_FUNCTION_CODE = "03"
    _READ_MAX_RETRY_TIME_SECONDS = 60

    def __init__(self, api_client: SolisCloudControlApiClient, inverter: Inverter) -> None:
        self._api_client = api_client
        self._inverter = inverter

    async def read_all(self) -> dict[int, int | None]:
        """Read raw Remote Dispatch holding registers; empty when Remote Dispatch is unavailable."""
        inverter = self._inverter
        if inverter.remote_dispatch_master is None:
            return {}

        serial_number = inverter.info.serial_number
        try:
            holding_words = await self._api_client.read_registers(
                serial_number,
                HOLDING_START,
                function_code=self._HOLDING_FUNCTION_CODE,
                register_number=HOLDING_COUNT,
                max_retry_time=self._READ_MAX_RETRY_TIME_SECONDS,
            )
        except SolisCloudControlApiError as error:
            raise RegisterServiceError(str(error)) from error

        return {HOLDING_START + offset: to_u16(word) for offset, word in enumerate(holding_words)}

    async def write(self, writes: Sequence[RegisterWrite]) -> None:
        """Send prepared holding-register blocks."""
        serial_number = self._inverter.info.serial_number
        for write in writes:
            frame = build_write_registers_frame(write.address, write.words)
            try:
                await self._api_client.control_at_command(serial_number, frame)
            except SolisCloudControlApiError as error:
                raise RegisterServiceError(str(error)) from error
