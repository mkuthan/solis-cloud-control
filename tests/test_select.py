import pytest
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from custom_components.solis_cloud_control.domain.storage_mode import StorageMode
from custom_components.solis_cloud_control.inverters.inverter import Inverter


@pytest.fixture
def storage_mode_entity_id(any_inverter: Inverter) -> str:
    return f"select.inverter_control_{any_inverter.info.serial_number}_storage_mode"


class TestStorageModeSelectIntegration:
    async def test_entity_registered(self, hass: HomeAssistant, setup_integration, storage_mode_entity_id: str):  # noqa: ARG002
        state = hass.states.get(storage_mode_entity_id)
        assert state is not None
        assert state.attributes.get("options") == ["Self-Use", "Feed-In Priority", "Off-Grid"]

    @pytest.mark.parametrize(
        ("value", "expected_mode"),
        [
            (str(1 << StorageMode.BIT_SELF_USE), "Self-Use"),
            (str(1 << StorageMode.BIT_FEED_IN_PRIORITY), "Feed-In Priority"),
            (str(1 << StorageMode.BIT_OFF_GRID), "Off-Grid"),
        ],
    )
    async def test_current_option_valid(
        self,
        hass: HomeAssistant,
        setup_integration,
        any_inverter: Inverter,
        storage_mode_entity_id: str,
        value,
        expected_mode,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.storage_mode.cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(storage_mode_entity_id)
        assert state.state == expected_mode

    @pytest.mark.parametrize(
        "value",
        [
            str(0),
            "not a number",
            None,
        ],
    )
    async def test_current_option_invalid(
        self,
        hass: HomeAssistant,
        setup_integration,
        any_inverter: Inverter,
        storage_mode_entity_id: str,
        value,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.storage_mode.cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(storage_mode_entity_id)
        assert state.state in ("unavailable", "unknown")

    @pytest.mark.parametrize(
        ("mode", "expected_value"),
        [
            ("Self-Use", str(1 << StorageMode.BIT_SELF_USE)),
            ("Feed-In Priority", str(1 << StorageMode.BIT_FEED_IN_PRIORITY)),
            ("Off-Grid", str(1 << StorageMode.BIT_OFF_GRID)),
        ],
    )
    async def test_async_select_option(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        storage_mode_entity_id: str,
        mode,
        expected_value,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.storage_mode.cid
        new_data = dict(coordinator.data)
        new_data[cid] = str(0)

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SELECT,
            "select_option",
            {"entity_id": storage_mode_entity_id, "option": mode},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            expected_value,
            None,
        )

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
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        storage_mode_entity_id: str,
        initial_value,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.storage_mode.cid
        new_data = dict(coordinator.data)
        new_data[cid] = initial_value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SELECT,
            "select_option",
            {"entity_id": storage_mode_entity_id, "option": "Self-Use"},
            blocking=True,
        )

        mock_api_client.control.assert_not_awaited()
