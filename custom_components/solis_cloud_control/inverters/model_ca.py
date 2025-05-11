from custom_components.solis_cloud_control.api import SolisCloudControlApiClient
from custom_components.solis_cloud_control.inverters.default_hybrid_inverter import create_default_hybrid_inverter
from custom_components.solis_cloud_control.inverters.inverter import Inverter, InverterInfo, InverterMaxExportPower


# RHI-3P(3-10)K-HVES-5G
async def create_inverter(api_client: SolisCloudControlApiClient, inverter_info: InverterInfo) -> Inverter:
    inverter = await create_default_hybrid_inverter(api_client, inverter_info)

    power = inverter_info.power if inverter_info.power is not None else 10_000
    inverter.max_export_power = InverterMaxExportPower(max_value=power)

    return inverter
