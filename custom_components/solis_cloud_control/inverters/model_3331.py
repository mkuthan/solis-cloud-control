from custom_components.solis_cloud_control.api import SolisCloudControlApiClient
from custom_components.solis_cloud_control.inverters.default_hybrid_inverter import create_default_hybrid_inverter
from custom_components.solis_cloud_control.inverters.inverter import Inverter, InverterInfo, InverterMaxExportPower


# S6-EH3P(8-15)K02-NV-YD-L
async def create_inverter(api_client: SolisCloudControlApiClient, inverter_info: InverterInfo) -> Inverter:
    inverter = await create_default_hybrid_inverter(api_client, inverter_info)

    power = inverter_info.power if inverter_info.power is not None else 15_000
    inverter.max_export_power = InverterMaxExportPower(max_value=power, step=100, scale=0.01)

    return inverter
