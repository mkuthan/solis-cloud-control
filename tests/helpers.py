from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from unittest.mock import AsyncMock

    from homeassistant.const import Platform
    from homeassistant.core import HomeAssistant, State

    from custom_components.solis_cloud_control.inverters.inverter import Inverter

type SetData = Callable[[dict[int, str | None]], Awaitable[None]]

type GetEntityId = Callable[[Platform, str], str]


def ensure[T](value: T | None) -> T:
    assert value is not None
    return value


def get_state(hass: HomeAssistant, entity_id: str) -> State:
    state = hass.states.get(entity_id)
    assert state is not None, f"entity '{entity_id}' is not registered"
    return state


def assert_control(
    mock_api_client: AsyncMock,
    inverter: Inverter,
    cid: int,
    value: str,
    old_value: str | None = None,
) -> None:
    mock_api_client.control.assert_awaited_once_with(inverter.info.serial_number, cid, value, old_value)
