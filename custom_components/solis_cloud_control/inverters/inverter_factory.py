import importlib
import logging

from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient
from custom_components.solis_cloud_control.inverters.inverter import Inverter, InverterInfo
from custom_components.solis_cloud_control.utils.safe_converters import safe_convert_power_to_watts

_LOGGER = logging.getLogger(__name__)


async def create_inverter_info(api_client: SolisCloudControlApiClient, inverter_sn: str) -> InverterInfo:
    inverter_details = await api_client.inverter_details(inverter_sn)

    model = str(inverter_details.get("model", "Unknown"))
    version = str(inverter_details.get("version", "Unknown"))
    machine = str(inverter_details.get("machine", "Unknown"))
    power = safe_convert_power_to_watts(inverter_details.get("power"), inverter_details.get("powerStr"))

    return InverterInfo(
        serial_number=inverter_sn,
        model=model,
        version=version,
        machine=machine,
        power=power,
    )


async def create_inverter(api_client: SolisCloudControlApiClient, inverter_info: InverterInfo) -> Inverter:
    try:
        inverter_model = inverter_info.model.lower()
        module_name = f"custom_components.solis_cloud_control.inverters.model_{inverter_model}"
        model_module = importlib.import_module(module_name)
        inverter = await model_module.create_inverter(inverter_info, api_client)
        _LOGGER.info("Inverter model '%s' created", inverter_info.model)
        return inverter
    except ImportError:
        _LOGGER.warning("Unknown inverter model '%s', fallback to generic hybrid inverter", inverter_info.model)
        return Inverter(inverter_info)
