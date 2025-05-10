from homeassistant.const import CONF_API_KEY, CONF_API_TOKEN

from custom_components.solis_cloud_control.const import CONF_INVERTER_SN
from custom_components.solis_cloud_control.data import SolisCloudControlData
from custom_components.solis_cloud_control.diagnostics import async_get_config_entry_diagnostics


async def test_diagnostics(hass, mock_coordinator, mock_config_entry, any_inverter) -> None:
    mock_coordinator.data = {-1: "any value"}
    mock_config_entry.runtime_data = SolisCloudControlData(inverter=any_inverter, coordinator=mock_coordinator)

    diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)
    assert diagnostics == {
        "entry_data": {
            CONF_API_KEY: "**REDACTED**",
            CONF_API_TOKEN: "**REDACTED**",
            CONF_INVERTER_SN: "any_inverter_sn",
        },
        "inverter_info": any_inverter.info,
        "coordinator_data": mock_coordinator.data,
    }
