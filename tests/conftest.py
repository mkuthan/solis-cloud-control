from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.solis_cloud_control.const import CONF_INVERTER_SN


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
