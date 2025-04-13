from unittest.mock import AsyncMock, Mock

import pytest
from pytest_socket import enable_socket, socket_allow_hosts

from custom_components.solis_cloud_control.const import CONF_INVERTER_SN


# https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/issues/154
@pytest.hookimpl(trylast=True)
def pytest_runtest_setup():
    enable_socket()
    socket_allow_hosts(["127.0.0.1", "localhost", "::1"], allow_unix_socket=True)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


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
