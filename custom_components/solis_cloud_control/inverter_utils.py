from custom_components.solis_cloud_control.api import SolisCloudControlApiClient

_CHARGE_DISCHARGE_MODE_CID = 6798
_CHARGE_DISCHARGE_MODE_SLOTS_ENABLED = 43605  # 0xAA55


async def charge_discharge_mode_slots_enabled(api_client: SolisCloudControlApiClient, inverter_sn: str) -> bool:
    charge_discharge_mode = await api_client.read(inverter_sn, _CHARGE_DISCHARGE_MODE_CID)
    return charge_discharge_mode == str(_CHARGE_DISCHARGE_MODE_SLOTS_ENABLED)
