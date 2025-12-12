from dataclasses import asdict

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry

_TO_REDACT = ["serial_number"]


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: SolisCloudControlConfigEntry,
) -> dict:
    return {
        "inverter_info": async_redact_data(asdict(config_entry.runtime_data.inverter.info), _TO_REDACT),
        "coordinator_data": config_entry.runtime_data.coordinator.data,
    }
