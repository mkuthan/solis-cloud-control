from dataclasses import replace

from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient
from custom_components.solis_cloud_control.inverters.inverter import Inverter, InverterInfo, InverterMaxExportPower


async def create_inverter(
    inverter_info: InverterInfo,
    api_client: SolisCloudControlApiClient,
) -> Inverter:
    inverter = await Inverter.create_hybrid_inverter(inverter_info, api_client)

    power = inverter_info.power_watts if inverter_info.power_watts is not None else 10_000
    inverter = replace(inverter, max_export_power=InverterMaxExportPower(max_value=power))

    return inverter
