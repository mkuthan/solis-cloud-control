from typing import TYPE_CHECKING

import pytest
from homeassistant.const import Platform

from custom_components.solis_cloud_control.domain.storage_mode import StorageMode
from tests.helpers import GetEntityId, SetData, assert_control, ensure, get_state

if TYPE_CHECKING:
    from unittest.mock import AsyncMock

    from homeassistant.core import HomeAssistant

    from custom_components.solis_cloud_control.inverters.inverter import Inverter


@pytest.fixture
def storage_mode_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.SELECT, "storage_mode")


class TestStorageModeSelectIntegration:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(self, hass: HomeAssistant, storage_mode_entity_id: str) -> None:
        state = hass.states.get(storage_mode_entity_id)
        assert state is not None
        assert state.attributes.get("options") == ["Self-Use", "Feed-In Priority", "Off-Grid", "Peak-Shaving"]

    @pytest.mark.parametrize(
        ("value", "expected_mode"),
        [
            (str(1 << StorageMode.BIT_SELF_USE), "Self-Use"),
            (str(1 << StorageMode.BIT_FEED_IN_PRIORITY), "Feed-In Priority"),
            (str(1 << StorageMode.BIT_OFF_GRID), "Off-Grid"),
            (str(1 << StorageMode.BIT_PEAK_SHAVING), "Peak-Shaving"),
        ],
    )
    async def test_current_option_valid(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        storage_mode_entity_id: str,
        value: str,
        expected_mode: str,
    ) -> None:
        cid = ensure(any_inverter.storage_mode).cid
        await set_data({cid: value})

        state = get_state(hass, storage_mode_entity_id)
        assert state.state == expected_mode

    @pytest.mark.parametrize(
        ("value", "expected_state"),
        [
            (str(0), "unknown"),
            ("not a number", "unknown"),
            (None, "unavailable"),
        ],
    )
    async def test_current_option_invalid(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        storage_mode_entity_id: str,
        value: None | str,
        expected_state: str,
    ) -> None:
        cid = ensure(any_inverter.storage_mode).cid
        await set_data({cid: value})

        state = get_state(hass, storage_mode_entity_id)
        assert state.state == expected_state

    @pytest.mark.parametrize(
        ("mode", "expected_value"),
        [
            ("Self-Use", str(1 << StorageMode.BIT_SELF_USE)),
            ("Feed-In Priority", str(1 << StorageMode.BIT_FEED_IN_PRIORITY)),
            ("Off-Grid", str(1 << StorageMode.BIT_OFF_GRID)),
            ("Peak-Shaving", str(1 << StorageMode.BIT_PEAK_SHAVING)),
        ],
    )
    async def test_async_select_option(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        storage_mode_entity_id: str,
        mode: str,
        expected_value: str,
    ) -> None:
        cid = ensure(any_inverter.storage_mode).cid
        await set_data({cid: str(0)})

        await hass.services.async_call(
            Platform.SELECT,
            "select_option",
            {"entity_id": storage_mode_entity_id, "option": mode},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, expected_value)

    @pytest.mark.parametrize(
        ("initial_mode", "expected_value"),
        [
            # Self-Use + grid charging -> Peak-Shaving + grid charging
            (
                str((1 << StorageMode.BIT_SELF_USE) | (1 << StorageMode.BIT_GRID_CHARGING)),
                str((1 << StorageMode.BIT_PEAK_SHAVING) | (1 << StorageMode.BIT_GRID_CHARGING)),
            ),
            # Feed-In Priority + grid charging -> Peak-Shaving + grid charging
            (
                str((1 << StorageMode.BIT_FEED_IN_PRIORITY) | (1 << StorageMode.BIT_GRID_CHARGING)),
                str((1 << StorageMode.BIT_PEAK_SHAVING) | (1 << StorageMode.BIT_GRID_CHARGING)),
            ),
        ],
    )
    async def test_async_select_peak_shaving_clears_other_base_modes(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        storage_mode_entity_id: str,
        initial_mode: str,
        expected_value: str,
    ) -> None:
        cid = ensure(any_inverter.storage_mode).cid
        await set_data({cid: initial_mode})

        await hass.services.async_call(
            Platform.SELECT,
            "select_option",
            {"entity_id": storage_mode_entity_id, "option": "Peak-Shaving"},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, expected_value)

    @pytest.mark.parametrize(
        "initial_value",
        [
            "not a number",
            None,
        ],
    )
    async def test_async_select_option_invalid_initial(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        storage_mode_entity_id: str,
        initial_value: None | str,
    ) -> None:
        cid = ensure(any_inverter.storage_mode).cid
        await set_data({cid: initial_value})

        await hass.services.async_call(
            Platform.SELECT,
            "select_option",
            {"entity_id": storage_mode_entity_id, "option": "Self-Use"},
            blocking=True,
        )

        mock_api_client.control.assert_not_awaited()
