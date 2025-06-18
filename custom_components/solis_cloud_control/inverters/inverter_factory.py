import importlib
import logging

from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient
from custom_components.solis_cloud_control.inverters.inverter import Inverter, InverterInfo

_LOGGER = logging.getLogger(__name__)

_INVERTER_REGISTRY = {
    "0200": "s6_gr1p_2_5_6_k",
    "0205": "s6_gr1p_2_5_6_k",
    "0507": "s5_gr3p_3_20_k",
    "3101": "s5_eh1p_3_6_k_l",
    "3102": "s5_eh1p_3_6_k_l",
    "3306": "s6_eh3p_5_10_k_h",
    "3331": "s6_eh3p_8_15_k02_nv_yd_l",
    "ca": "rhi_3p_3_10_k_hves_5g",
    "f4": "rhi_3_6_k_48es_5g",
}


async def create_inverter_info(api_client: SolisCloudControlApiClient, inverter_sn: str) -> InverterInfo:
    inverter_details = await api_client.inverter_details(inverter_sn)

    return InverterInfo(
        serial_number=inverter_sn,
        model=_get_inverter_detail(inverter_details, "model"),
        version=_get_inverter_detail(inverter_details, "version"),
        machine=_get_inverter_detail(inverter_details, "machine"),
        energy_storage_control=_get_inverter_detail(inverter_details, "energyStorageControl"),
        smart_support=_get_inverter_detail(inverter_details, "smartSupport"),
        generator_support=_get_inverter_detail(inverter_details, "generatorSupport"),
        collector_model=_get_inverter_detail(inverter_details, "collectorModel"),
        power=_get_inverter_detail(inverter_details, "power"),
        power_unit=_get_inverter_detail(inverter_details, "powerStr"),
    )


async def create_inverter(api_client: SolisCloudControlApiClient, inverter_info: InverterInfo) -> Inverter:
    inverter_model_id = inverter_info.model.lower()
    inverter_model = _INVERTER_REGISTRY.get(inverter_model_id)

    if inverter_model is not None:
        _LOGGER.info("Supported inverter model '%s' found", inverter_model.upper())
        module_name = f"custom_components.solis_cloud_control.inverters.model_{inverter_model}"
        model_module = importlib.import_module(module_name)
        return await model_module.create_inverter(inverter_info, api_client)
    else:
        if inverter_info.is_string_inverter:
            _LOGGER.warning("Unknown inverter model '%s', fallback to generic string inverter", inverter_info.model)
            return await Inverter.create_string_inverter(inverter_info, api_client)
        else:
            _LOGGER.warning("Unknown inverter model '%s', fallback to generic hybrid inverter", inverter_info.model)
            return await Inverter.create_hybrid_inverter(inverter_info, api_client)


def _get_inverter_detail(inverter_details: dict[str, any], field: str) -> str | None:
    return str(value) if (value := inverter_details.get(field)) is not None else None
