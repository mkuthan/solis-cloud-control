from datetime import datetime
from typing import TYPE_CHECKING

import pytest
from homeassistant.const import Platform

from tests.helpers import GetEntityId, SetData, assert_control, ensure, get_state

if TYPE_CHECKING:
    from unittest.mock import AsyncMock

    from homeassistant.core import HomeAssistant

    from custom_components.solis_cloud_control.inverters.inverter import Inverter


@pytest.fixture
def inverter_time_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.DATETIME, "inverter_time")


class TestInverterTimeEntity:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        inverter_time_entity_id: str,
    ) -> None:
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
        set_data: SetData,
        any_inverter: Inverter,
        inverter_time_entity_id: str,
        value: str,
        timezone: str,
        expected: str,
    ) -> None:
        await hass.config.async_set_time_zone(timezone)
        await set_data({ensure(any_inverter.time).cid: value})

        # HA reports the state in UTC, so compare instants rather than strings
        state = get_state(hass, inverter_time_entity_id)
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
        set_data: SetData,
        any_inverter: Inverter,
        inverter_time_entity_id: str,
        value: None | str,
        expected_state: str,
    ) -> None:
        await set_data({ensure(any_inverter.time).cid: value})

        state = get_state(hass, inverter_time_entity_id)
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
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        inverter_time_entity_id: str,
        value: str,
        timezone: str,
        expected: str,
    ) -> None:
        await hass.config.async_set_time_zone(timezone)
        await set_data({ensure(any_inverter.time).cid: "2025-01-01 00:00:00"})

        await hass.services.async_call(
            Platform.DATETIME,
            "set_value",
            {"entity_id": inverter_time_entity_id, "datetime": value},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, ensure(any_inverter.time).cid, expected)
