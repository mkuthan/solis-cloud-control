from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.const import CONF_API_KEY, CONF_API_TOKEN
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_socket import enable_socket, socket_allow_hosts

from custom_components.solis_cloud_control.const import CONF_INVERTER_SN, DOMAIN
from custom_components.solis_cloud_control.inverters.inverter import (
    Inverter,
    InverterInfo,
)


# https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/issues/154
@pytest.hookimpl(trylast=True)
def pytest_runtest_setup():
    enable_socket()
    socket_allow_hosts(["127.0.0.1", "localhost", "::1"], allow_unix_socket=True)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def mock_api_client():
    return AsyncMock()


@pytest.fixture
def mock_coordinator():
    coordinator = Mock()
    coordinator.control = AsyncMock()
    coordinator.data = {}
    coordinator.config_entry = Mock()
    coordinator.config_entry.entry_id = "any_entry_id"
    coordinator.config_entry.domain = "any_domain"
    coordinator.config_entry.data = {CONF_INVERTER_SN: "any_inverter_sn"}
    return coordinator


@pytest.fixture
def mock_config_entry(hass):
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        data={
            CONF_API_KEY: "any_api_key",
            CONF_API_TOKEN: "any_api_token",
            CONF_INVERTER_SN: "any_inverter_sn",
        },
    )
    config_entry.add_to_hass(hass)
    return config_entry


@pytest.fixture
def any_inverter_info():
    return InverterInfo(
        serial_number="any_inverter_sn",
        model="any_model",
        machine="any_machine",
        version="any_version",
        power=None,
    )


@pytest.fixture
def any_inverter(any_inverter_info: InverterInfo) -> Inverter:
    return Inverter(info=any_inverter_info)
