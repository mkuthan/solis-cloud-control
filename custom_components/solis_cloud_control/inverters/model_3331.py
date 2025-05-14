from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient
from custom_components.solis_cloud_control.inverters.inverter import Inverter, InverterInfo, InverterMaxExportPower


# S6-EH3P(8-15)K02-NV-YD-L
async def create_inverter(
    inverter_info: InverterInfo,
    api_client: SolisCloudControlApiClient,  # noqa: ARG001
) -> Inverter:
    inverter = Inverter(inverter_info)

    power = inverter_info.power if inverter_info.power is not None else 15_000
    inverter.max_export_power = InverterMaxExportPower(max_value=power, step=100, scale=0.01)

    return inverter
