from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient
from custom_components.solis_cloud_control.inverters.inverter import Inverter, InverterInfo


async def create_inverter(
    inverter_info: InverterInfo,
    api_client: SolisCloudControlApiClient,
) -> Inverter:
    return await Inverter.create_string_inverter(inverter_info, api_client)
