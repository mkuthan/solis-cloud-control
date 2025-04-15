from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_API_KEY, CONF_API_TOKEN
from homeassistant.core import HomeAssistant

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry

_TO_REDACT = [
    CONF_API_KEY,
    CONF_API_TOKEN,
]


async def async_get_config_entry_diagnostics(
    _hass: HomeAssistant, config_entry: SolisCloudControlConfigEntry
) -> dict[str, any]:
    return {
        "entry_data": async_redact_data(config_entry.data, _TO_REDACT),
        "data": config_entry.runtime_data.coordinator.data,
    }
