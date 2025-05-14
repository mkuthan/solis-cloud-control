from unittest.mock import patch

import pytest
from homeassistant.const import CONF_API_KEY, CONF_API_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiError
from custom_components.solis_cloud_control.const import CONF_INVERTER_SN, DOMAIN

_TEST_API_KEY = "any api key"
_TEST_API_TOKEN = "any api token"
_TEST_INVERTER_SN = "any inverter sn"


@pytest.fixture
def user_step_input() -> dict[str, str]:
    return {CONF_API_KEY: _TEST_API_KEY, CONF_API_TOKEN: _TEST_API_TOKEN}


@pytest.fixture
def inverter_select_step_input() -> dict[str, str]:
    return {CONF_INVERTER_SN: _TEST_INVERTER_SN}


@pytest.fixture
async def config_flow_init(hass: HomeAssistant):
    return await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})


@pytest.fixture
def flow_id(config_flow_init) -> str:
    return config_flow_init["flow_id"]


@pytest.fixture
def mock_setup_entry():
    with patch(
        "custom_components.solis_cloud_control.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        yield mock_setup


async def test_all_steps(
    hass: HomeAssistant, flow_id, user_step_input, inverter_select_step_input, mock_setup_entry
) -> None:
    inverters = [{"sn": _TEST_INVERTER_SN, "stationName": "any test station name"}]

    with patch(
        "custom_components.solis_cloud_control.config_flow.SolisCloudControlFlowHandler._inverter_list",
        return_value=inverters,
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            user_input=user_step_input,
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "select_inverter"

        result = await hass.config_entries.flow.async_configure(
            flow_id,
            user_input=inverter_select_step_input,
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == f"Inverter {_TEST_INVERTER_SN}"
        assert result["data"] == {
            CONF_API_KEY: _TEST_API_KEY,
            CONF_API_TOKEN: _TEST_API_TOKEN,
            CONF_INVERTER_SN: _TEST_INVERTER_SN,
        }


async def test_all_steps_duplicate_inverter(
    hass: HomeAssistant, flow_id, user_step_input, inverter_select_step_input, mock_setup_entry
) -> None:
    inverters = [{"sn": _TEST_INVERTER_SN, "stationName": "any test station name"}]

    with patch(
        "custom_components.solis_cloud_control.config_flow.SolisCloudControlFlowHandler._inverter_list",
        return_value=inverters,
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            user_input=user_step_input,
        )
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            user_input=inverter_select_step_input,
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY

    # add the same inverter again
    with patch(
        "custom_components.solis_cloud_control.config_flow.SolisCloudControlFlowHandler._inverter_list",
        return_value=inverters,
    ):
        config_flow = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(
            config_flow["flow_id"],
            user_input=user_step_input,
        )
        result = await hass.config_entries.flow.async_configure(
            config_flow["flow_id"],
            user_input=inverter_select_step_input,
        )
        assert result["type"] == FlowResultType.ABORT


async def test_flow_user_step_unknown_error(hass: HomeAssistant, flow_id, user_step_input) -> None:
    with patch(
        "custom_components.solis_cloud_control.config_flow.SolisCloudControlFlowHandler._inverter_list",
        side_effect=Exception("any error"),
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            user_input=user_step_input,
        )
        assert result["errors"] == {"base": "unknown"}


async def test_flow_user_step_cannot_connect(hass: HomeAssistant, flow_id, user_step_input) -> None:
    with patch(
        "custom_components.solis_cloud_control.config_flow.SolisCloudControlFlowHandler._inverter_list",
        side_effect=SolisCloudControlApiError("any error"),
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            user_input=user_step_input,
        )
        assert result["errors"] == {"base": "cannot_connect"}


async def test_flow_user_step_invalid_auth(hass: HomeAssistant, flow_id, user_step_input) -> None:
    with patch(
        "custom_components.solis_cloud_control.config_flow.SolisCloudControlFlowHandler._inverter_list",
        side_effect=SolisCloudControlApiError("any error", response_code="Z0001"),
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            user_input=user_step_input,
        )
        assert result["errors"] == {"base": "invalid_auth"}


async def test_flow_user_step_no_inverters(hass: HomeAssistant, flow_id, user_step_input) -> None:
    with patch(
        "custom_components.solis_cloud_control.config_flow.SolisCloudControlFlowHandler._inverter_list",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            user_input=user_step_input,
        )
        assert result["errors"] == {"base": "no_inverters"}


async def test_flow_user_step_inverter_without_sn(hass: HomeAssistant, flow_id, user_step_input) -> None:
    with patch(
        "custom_components.solis_cloud_control.config_flow.SolisCloudControlFlowHandler._inverter_list",
        return_value=[{"stationName": "any test station name"}],
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id,
            user_input=user_step_input,
        )
        assert result["errors"] == {"base": "no_inverters"}
