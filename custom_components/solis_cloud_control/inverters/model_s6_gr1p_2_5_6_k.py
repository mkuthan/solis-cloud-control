from dataclasses import replace

from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient
from custom_components.solis_cloud_control.inverters.inverter import Inverter, InverterInfo, InverterPowerLimit


async def create_inverter(
    inverter_info: InverterInfo,
    api_client: SolisCloudControlApiClient,  # noqa: ARG001
) -> Inverter:
    inverter = Inverter.create_string_inverter(inverter_info)

    inverter = replace(inverter, power_limit=InverterPowerLimit(max_value=110))

    return inverter
