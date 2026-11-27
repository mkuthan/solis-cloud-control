from typing import TYPE_CHECKING

from custom_components.solis_cloud_control.api.solis_api_error import SolisCloudControlApiError

if TYPE_CHECKING:
    from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient
    from custom_components.solis_cloud_control.inverters.inverter import Inverter


class CidServiceError(Exception):
    pass


class CidService:
    _READ_BATCH_MAX_RETRY_TIME_SECONDS = 180
    _READ_MAX_RETRY_TIME_SECONDS = 60

    def __init__(self, api_client: SolisCloudControlApiClient, inverter: Inverter) -> None:
        self._api_client = api_client
        self._inverter = inverter

    async def read_all(self) -> dict[int, str | None]:
        inverter_sn = self._inverter.info.serial_number
        try:
            results = await self._api_client.read_batch(
                inverter_sn,
                self._read_batch_cids(),
                max_retry_time=self._READ_BATCH_MAX_RETRY_TIME_SECONDS,
            )

            for read_cid in self._read_cids():
                results[read_cid] = await self._api_client.read(
                    inverter_sn,
                    read_cid,
                    max_retry_time=self._READ_MAX_RETRY_TIME_SECONDS,
                )
            return {cid: results.get(cid) for cid in [*self._read_batch_cids(), *self._read_cids()]}
        except SolisCloudControlApiError as error:
            raise CidServiceError(str(error)) from error

    async def control(
        self,
        cid: int,
        value: str,
        old_value: str | None = None,
    ) -> None:
        inverter_sn = self._inverter.info.serial_number
        try:
            await self._api_client.control(inverter_sn, cid, value, old_value)
        except SolisCloudControlApiError as error:
            raise CidServiceError(str(error)) from error

    def _read_batch_cids(self) -> list[int]:
        inverter = self._inverter
        cids: list[int] = []

        if inverter.on_off:
            cids.append(inverter.on_off.on_cid)
            cids.append(inverter.on_off.off_cid)
        if inverter.time:
            cids.append(inverter.time.cid)
        if inverter.storage_mode:
            cids.append(inverter.storage_mode.cid)
        if inverter.charge_discharge_slots:
            cids.extend(inverter.charge_discharge_slots.all_cids)
        if inverter.max_output_power:
            cids.append(inverter.max_output_power.cid)
        if inverter.max_export_power:
            cids.append(inverter.max_export_power.cid)
        if inverter.export_calibration:
            cids.append(inverter.export_calibration.cid)
        if inverter.power_limit:
            cids.append(inverter.power_limit.cid)
        if inverter.allow_export:
            cids.append(inverter.allow_export.cid)
        if inverter.battery_reserve_soc:
            cids.append(inverter.battery_reserve_soc.cid)
        if inverter.battery_over_discharge_soc:
            cids.append(inverter.battery_over_discharge_soc.cid)
        if inverter.battery_force_charge_soc:
            cids.append(inverter.battery_force_charge_soc.cid)
        if inverter.battery_recovery_soc:
            cids.append(inverter.battery_recovery_soc.cid)
        if inverter.battery_max_charge_soc:
            cids.append(inverter.battery_max_charge_soc.cid)
        if inverter.battery_max_charge_current:
            cids.append(inverter.battery_max_charge_current.cid)
        if inverter.battery_max_discharge_current:
            cids.append(inverter.battery_max_discharge_current.cid)
        if inverter.mppt_scan_interval:
            cids.append(inverter.mppt_scan_interval.cid)
        if inverter.mppt_scanning:
            cids.append(inverter.mppt_scanning.cid)
        if inverter.peak_shaving_max_usable_grid_power:
            cids.append(inverter.peak_shaving_max_usable_grid_power.cid)
        if inverter.peak_shaving_baseline_soc:
            cids.append(inverter.peak_shaving_baseline_soc.cid)
        if inverter.grid_peak_shaving:
            cids.append(inverter.grid_peak_shaving.cid)
        if inverter.grid_peak_shaving_power:
            cids.append(inverter.grid_peak_shaving_power.cid)

        return cids

    def _read_cids(self) -> list[int]:
        inverter = self._inverter
        cids = []

        if inverter.charge_discharge_settings:
            cids.append(inverter.charge_discharge_settings.cid)

        return cids
