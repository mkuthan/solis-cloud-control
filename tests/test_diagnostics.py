from homeassistant.const import CONF_API_KEY, CONF_API_TOKEN
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solis_cloud_control.const import CONF_INVERTER_SN, DOMAIN
from custom_components.solis_cloud_control.data import SolisCloudControlData
from custom_components.solis_cloud_control.diagnostics import async_get_config_entry_diagnostics


async def test_diagnostics(hass, mock_coordinator) -> None:
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        data={
            CONF_API_KEY: "test_api_key",
            CONF_API_TOKEN: "test_api_token",
            CONF_INVERTER_SN: "test_inverter_sn",
        },
    )
    config_entry.add_to_hass(hass)

    any_data = {-1: "any value"}
    mock_coordinator.data = any_data
    config_entry.runtime_data = SolisCloudControlData(coordinator=mock_coordinator)

    diagnostics = await async_get_config_entry_diagnostics(hass, config_entry)
    assert diagnostics == {
        "entry_data": {
            CONF_API_KEY: "**REDACTED**",
            CONF_API_TOKEN: "**REDACTED**",
            CONF_INVERTER_SN: "test_inverter_sn",
        },
        "data": any_data,
    }
