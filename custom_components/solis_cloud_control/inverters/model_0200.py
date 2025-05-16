from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient
from custom_components.solis_cloud_control.inverters.inverter import Inverter, InverterInfo


# S6-GR1P(2.5-6)K
async def create_inverter(
    inverter_info: InverterInfo,
    api_client: SolisCloudControlApiClient,  # noqa: ARG001
) -> Inverter:
    return Inverter.create_string_inverter(inverter_info)
