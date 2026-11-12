from dataclasses import asdict
from typing import TYPE_CHECKING, cast

from custom_components.solis_cloud_control.data import SolisCloudControlData
from custom_components.solis_cloud_control.diagnostics import async_get_config_entry_diagnostics

if TYPE_CHECKING:
    from unittest.mock import Mock

    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry
    from custom_components.solis_cloud_control.inverters.inverter import Inverter


async def test_diagnostics(
    hass: HomeAssistant, mock_coordinator: Mock, mock_config_entry: MockConfigEntry, any_inverter: Inverter
) -> None:
    mock_coordinator.data = {1: "any value"}
    mock_config_entry.runtime_data = SolisCloudControlData(inverter=any_inverter, coordinator=mock_coordinator)

    diagnostics = await async_get_config_entry_diagnostics(
        hass, cast("SolisCloudControlConfigEntry", mock_config_entry)
    )

    expected_inverter_info = asdict(any_inverter.info)
    expected_inverter_info["serial_number"] = "**REDACTED**"

    assert diagnostics == {
        "inverter_info": expected_inverter_info,
        "coordinator_data": mock_coordinator.data,
    }
