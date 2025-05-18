import importlib
import logging

from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient
from custom_components.solis_cloud_control.inverters.inverter import Inverter, InverterInfo

_LOGGER = logging.getLogger(__name__)


async def create_inverter_info(api_client: SolisCloudControlApiClient, inverter_sn: str) -> InverterInfo:
    inverter_details = await api_client.inverter_details(inverter_sn)

    model = str(inverter_details.get("model", "Unknown"))
    version = str(inverter_details.get("version", "Unknown"))
    machine = str(inverter_details.get("machine", "Unknown"))
    type = str(inverter_details.get("inverterType", "Unknown"))
    smart_support = str(inverter_details.get("smartSupport", "Unknown"))
    generator_support = str(inverter_details.get("generatorSupport", "Unknown"))
    battery_num = str(inverter_details.get("batteryNum", "Unknown"))
    power = str(inverter_details.get("power", "Unknown"))
    power_unit = str(inverter_details.get("powerStr", "Unknown"))

    return InverterInfo(
        serial_number=inverter_sn,
        model=model,
        version=version,
        machine=machine,
        type=type,
        smart_support=smart_support,
        generator_support=generator_support,
        battery_num=battery_num,
        power=power,
        power_unit=power_unit,
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
