from datetime import datetime

import pytest
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from custom_components.solis_cloud_control.inverters.inverter import Inverter


@pytest.fixture
def inverter_time_entity_id(get_entity_id) -> str:
    return get_entity_id(Platform.DATETIME, "inverter_time")


class TestInverterTimeEntity:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        inverter_time_entity_id: str,
    ):
        state = hass.states.get(inverter_time_entity_id)
        assert state is not None

    @pytest.mark.parametrize(
        ("value", "timezone", "expected"),
        [
            ("2025-12-11 17:00:00", "UTC", "2025-12-11T17:00:00+00:00"),
            ("2025-12-11 17:00:00", "Europe/Warsaw", "2025-12-11T17:00:00+01:00"),
        ],
    )
    async def test_state_from_coordinator(
        self,
        hass: HomeAssistant,
        set_data,
        any_inverter: Inverter,
        inverter_time_entity_id: str,
        value: str,
        timezone: str,
        expected: str,
    ):
        await hass.config.async_set_time_zone(timezone)
        await set_data({any_inverter.time.cid: value})

        # HA reports the state in UTC, so compare instants rather than strings
        state = hass.states.get(inverter_time_entity_id)
        assert datetime.fromisoformat(state.state) == datetime.fromisoformat(expected)

    @pytest.mark.parametrize(
        ("value", "expected_state"),
        [
            ("invalid", "unknown"),
            (None, "unavailable"),
        ],
    )
    async def test_state_invalid(
        self,
        hass: HomeAssistant,
        set_data,
        any_inverter: Inverter,
        inverter_time_entity_id: str,
        value,
        expected_state: str,
    ):
        await set_data({any_inverter.time.cid: value})

        state = hass.states.get(inverter_time_entity_id)
        assert state.state == expected_state

    @pytest.mark.parametrize(
        ("value", "timezone", "expected"),
        [
            ("2025-12-11T17:00:00+00:00", "UTC", "2025-12-11 17:00:00"),
            ("2025-12-11T17:00:00+01:00", "Europe/Warsaw", "2025-12-11 17:00:00"),
        ],
    )
    async def test_async_set_value(
        self,
        hass: HomeAssistant,
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        inverter_time_entity_id: str,
        value: str,
        timezone: str,
        expected: str,
    ):
        await hass.config.async_set_time_zone(timezone)
        await set_data({any_inverter.time.cid: "2025-01-01 00:00:00"})

        await hass.services.async_call(
            Platform.DATETIME,
            "set_value",
            {"entity_id": inverter_time_entity_id, "datetime": value},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            any_inverter.time.cid,
            expected,
            None,
        )
