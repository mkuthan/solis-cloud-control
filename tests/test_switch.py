import pytest
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from custom_components.solis_cloud_control.domain.storage_mode import StorageMode
from custom_components.solis_cloud_control.inverters.inverter import Inverter


@pytest.fixture
def inverter_on_off_entity_id(any_inverter: Inverter) -> str:
    return f"switch.inverter_control_{any_inverter.info.serial_number}_inverter_on_off"


@pytest.fixture
def allow_export_entity_id(any_inverter: Inverter) -> str:
    return f"switch.inverter_control_{any_inverter.info.serial_number}_allow_export"


@pytest.fixture
def slot1_charge_switch_entity_id(any_inverter: Inverter) -> str:
    return f"switch.inverter_control_{any_inverter.info.serial_number}_slot1_charge"


@pytest.fixture
def slot1_discharge_switch_entity_id(any_inverter: Inverter) -> str:
    return f"switch.inverter_control_{any_inverter.info.serial_number}_slot1_discharge"


@pytest.fixture
def battery_reserve_entity_id(any_inverter: Inverter) -> str:
    return f"switch.inverter_control_{any_inverter.info.serial_number}_battery_reserve"


@pytest.fixture
def allow_grid_charging_entity_id(any_inverter: Inverter) -> str:
    return f"switch.inverter_control_{any_inverter.info.serial_number}_allow_grid_charging"


@pytest.fixture
def grid_peak_shaving_entity_id(any_inverter: Inverter) -> str:
    return f"switch.inverter_control_{any_inverter.info.serial_number}_grid_peak_shaving"


@pytest.fixture
def time_of_use_entity_id(any_inverter: Inverter) -> str:
    return f"switch.inverter_control_{any_inverter.info.serial_number}_time_of_use"


@pytest.fixture
def mppt_scanning_entity_id(any_inverter: Inverter) -> str:
    return f"switch.inverter_control_{any_inverter.info.serial_number}_mppt_multi_peak_scanning"


class TestOnOffSwitch:
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        inverter_on_off_entity_id: str,
    ):
        state = hass.states.get(inverter_on_off_entity_id)
        assert state is not None

    @pytest.mark.parametrize(
        ("on_value", "off_value", "expected_is_on"),
        [
            ("190", "190", True),
            ("222", "222", False),
            ("190", "222", None),
            ("0", "0", None),
        ],
    )
    async def test_state_from_coordinator(
        self,
        hass: HomeAssistant,
        setup_integration,
        any_inverter: Inverter,
        inverter_on_off_entity_id: str,
        on_value,
        off_value,
        expected_is_on,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        on_cid = any_inverter.on_off.on_cid
        off_cid = any_inverter.on_off.off_cid
        new_data = dict(coordinator.data)
        new_data[on_cid] = on_value
        new_data[off_cid] = off_value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(inverter_on_off_entity_id)
        assert state.state == "on" if expected_is_on else "off" if expected_is_on is False else "unknown"

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        inverter_on_off_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        on_cid = any_inverter.on_off.on_cid
        off_cid = any_inverter.on_off.off_cid
        new_data = dict(coordinator.data)
        new_data[on_cid] = "222"
        new_data[off_cid] = "222"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_on",
            {"entity_id": inverter_on_off_entity_id},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            on_cid,
            any_inverter.on_off.on_value,
            None,
        )

    async def test_turn_off(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        inverter_on_off_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        on_cid = any_inverter.on_off.on_cid
        off_cid = any_inverter.on_off.off_cid
        new_data = dict(coordinator.data)
        new_data[on_cid] = "190"
        new_data[off_cid] = "190"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_off",
            {"entity_id": inverter_on_off_entity_id},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            off_cid,
            any_inverter.on_off.off_value,
            None,
        )


class TestAllowExportSwitch:
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        allow_export_entity_id: str,
    ):
        state = hass.states.get(allow_export_entity_id)
        assert state is not None

    @pytest.mark.parametrize(
        ("value", "expected_is_on"),
        [
            ("0", True),
            ("1", False),
            (None, None),
        ],
    )
    async def test_state_from_coordinator(
        self,
        hass: HomeAssistant,
        setup_integration,
        any_inverter: Inverter,
        allow_export_entity_id: str,
        value,
        expected_is_on,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.allow_export.cid
        storage_cid = any_inverter.storage_mode.cid
        new_data = dict(coordinator.data)
        new_data[cid] = value
        new_data[storage_cid] = str(1 << StorageMode.BIT_SELF_USE)

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(allow_export_entity_id)
        assert state.state == "on" if expected_is_on else "off" if expected_is_on is False else "unknown"

    @pytest.mark.parametrize(
        ("storage_mode_value", "expected_available"),
        [
            (str(1 << StorageMode.BIT_SELF_USE), True),
            (str(1 << StorageMode.BIT_FEED_IN_PRIORITY), False),
            (str(1 << StorageMode.BIT_OFF_GRID), False),
            (None, False),
        ],
    )
    async def test_availability(
        self,
        hass: HomeAssistant,
        setup_integration,
        any_inverter: Inverter,
        allow_export_entity_id: str,
        storage_mode_value,
        expected_available,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        storage_cid = any_inverter.storage_mode.cid
        export_cid = any_inverter.allow_export.cid
        new_data = dict(coordinator.data)
        new_data[storage_cid] = storage_mode_value
        new_data[export_cid] = "0"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(allow_export_entity_id)
        assert state.state == "unavailable" if not expected_available else state.state != "unavailable"

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        allow_export_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.allow_export.cid
        storage_cid = any_inverter.storage_mode.cid
        new_data = dict(coordinator.data)
        new_data[cid] = "1"
        new_data[storage_cid] = str(1 << StorageMode.BIT_SELF_USE)

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_on",
            {"entity_id": allow_export_entity_id},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            "0",
            any_inverter.allow_export.off_value,
        )

    async def test_turn_off(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        allow_export_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.allow_export.cid
        storage_cid = any_inverter.storage_mode.cid
        new_data = dict(coordinator.data)
        new_data[cid] = "0"
        new_data[storage_cid] = str(1 << StorageMode.BIT_SELF_USE)

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_off",
            {"entity_id": allow_export_entity_id},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            "1",
            any_inverter.allow_export.on_value,
        )

    async def test_turn_on_when_none(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        allow_export_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.allow_export.cid
        storage_cid = any_inverter.storage_mode.cid
        new_data = dict(coordinator.data)
        new_data[cid] = None
        new_data[storage_cid] = str(1 << StorageMode.BIT_SELF_USE)

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_on",
            {"entity_id": allow_export_entity_id},
            blocking=True,
        )

        mock_api_client.control.assert_not_awaited()


class TestSlotV2Switch:
    async def test_charge_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        slot1_charge_switch_entity_id: str,
    ):
        state = hass.states.get(slot1_charge_switch_entity_id)
        assert state is not None

    async def test_discharge_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        slot1_discharge_switch_entity_id: str,
    ):
        state = hass.states.get(slot1_discharge_switch_entity_id)
        assert state is not None

    @pytest.mark.parametrize(
        ("value", "expected_is_on"),
        [
            ("1", True),
            ("0", False),
            (None, None),
        ],
    )
    async def test_charge_state_from_coordinator(
        self,
        hass: HomeAssistant,
        setup_integration,
        any_inverter: Inverter,
        slot1_charge_switch_entity_id: str,
        value,
        expected_is_on,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        slots = any_inverter.charge_discharge_slots
        cid = slots.charge_slot1.switch_cid

        # Set valid defaults for all CIDs to make entities available
        new_data = {}
        for slot in [
            slots.charge_slot1,
            slots.charge_slot2,
            slots.charge_slot3,
            slots.charge_slot4,
            slots.charge_slot5,
            slots.charge_slot6,
            slots.discharge_slot1,
            slots.discharge_slot2,
            slots.discharge_slot3,
            slots.discharge_slot4,
            slots.discharge_slot5,
            slots.discharge_slot6,
        ]:
            new_data[slot.switch_cid] = "0"
            new_data[slot.time_cid] = "00:00-00:00"
            new_data[slot.current_cid] = "0"
            new_data[slot.soc_cid] = "0"
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(slot1_charge_switch_entity_id)
        assert state.state == "on" if expected_is_on else "off" if expected_is_on is False else "unknown"

    async def test_charge_turn_on(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        slot1_charge_switch_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        slots = any_inverter.charge_discharge_slots
        cid = slots.charge_slot1.switch_cid

        # Set valid defaults for all CIDs to make entities available
        new_data = {}
        for slot in [
            slots.charge_slot1,
            slots.charge_slot2,
            slots.charge_slot3,
            slots.charge_slot4,
            slots.charge_slot5,
            slots.charge_slot6,
            slots.discharge_slot1,
            slots.discharge_slot2,
            slots.discharge_slot3,
            slots.discharge_slot4,
            slots.discharge_slot5,
            slots.discharge_slot6,
        ]:
            new_data[slot.switch_cid] = "0"
            new_data[slot.time_cid] = "00:00-00:00"
            new_data[slot.current_cid] = "0"
            new_data[slot.soc_cid] = "0"
        new_data[cid] = "0"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_on",
            {"entity_id": slot1_charge_switch_entity_id},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            "1",
            "0",
        )

    async def test_charge_turn_off(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        slot1_charge_switch_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        slots = any_inverter.charge_discharge_slots
        cid = slots.charge_slot1.switch_cid

        # Set valid defaults for all CIDs to make entities available
        new_data = {}
        for slot in [
            slots.charge_slot1,
            slots.charge_slot2,
            slots.charge_slot3,
            slots.charge_slot4,
            slots.charge_slot5,
            slots.charge_slot6,
            slots.discharge_slot1,
            slots.discharge_slot2,
            slots.discharge_slot3,
            slots.discharge_slot4,
            slots.discharge_slot5,
            slots.discharge_slot6,
        ]:
            new_data[slot.switch_cid] = "0"
            new_data[slot.time_cid] = "00:00-00:00"
            new_data[slot.current_cid] = "0"
            new_data[slot.soc_cid] = "0"
        new_data[cid] = "1"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_off",
            {"entity_id": slot1_charge_switch_entity_id},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            "0",
            "1",
        )


class TestBatteryReserveSwitch:
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        battery_reserve_entity_id: str,
    ):
        state = hass.states.get(battery_reserve_entity_id)
        assert state is not None

    @pytest.mark.parametrize(
        ("value", "expected_is_on"),
        [
            (str(1 << StorageMode.BIT_BACKUP_MODE), True),
            ("0", False),
            (None, None),
            ("not a number", None),
        ],
    )
    async def test_state_from_coordinator(
        self,
        hass: HomeAssistant,
        setup_integration,
        any_inverter: Inverter,
        battery_reserve_entity_id: str,
        value,
        expected_is_on,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.storage_mode.cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(battery_reserve_entity_id)
        assert state.state == "on" if expected_is_on else "off" if expected_is_on is False else "unknown"

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        battery_reserve_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.storage_mode.cid
        bit = StorageMode.BIT_BACKUP_MODE
        new_data = dict(coordinator.data)
        new_data[cid] = "0"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_on",
            {"entity_id": battery_reserve_entity_id},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            str(1 << bit),
            None,
        )

    async def test_turn_off(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        battery_reserve_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.storage_mode.cid
        bit = StorageMode.BIT_BACKUP_MODE
        new_data = dict(coordinator.data)
        new_data[cid] = str(1 << bit)

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_off",
            {"entity_id": battery_reserve_entity_id},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            str(0),
            None,
        )

    @pytest.mark.parametrize("initial_value", ["not a number", None])
    async def test_turn_on_off_invalid_initial(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        battery_reserve_entity_id: str,
        initial_value,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.storage_mode.cid
        new_data = dict(coordinator.data)
        new_data[cid] = initial_value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_on",
            {"entity_id": battery_reserve_entity_id},
            blocking=True,
        )
        await hass.services.async_call(
            Platform.SWITCH,
            "turn_off",
            {"entity_id": battery_reserve_entity_id},
            blocking=True,
        )

        mock_api_client.control.assert_not_awaited()


class TestAllowGridChargingSwitch:
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        allow_grid_charging_entity_id: str,
    ):
        state = hass.states.get(allow_grid_charging_entity_id)
        assert state is not None

    @pytest.mark.parametrize(
        ("value", "expected_is_on"),
        [
            (str(1 << StorageMode.BIT_GRID_CHARGING), True),
            ("0", False),
            (None, None),
        ],
    )
    async def test_state_from_coordinator(
        self,
        hass: HomeAssistant,
        setup_integration,
        any_inverter: Inverter,
        allow_grid_charging_entity_id: str,
        value,
        expected_is_on,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.storage_mode.cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(allow_grid_charging_entity_id)
        assert state.state == "on" if expected_is_on else "off" if expected_is_on is False else "unknown"

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        allow_grid_charging_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.storage_mode.cid
        bit = StorageMode.BIT_GRID_CHARGING
        new_data = dict(coordinator.data)
        new_data[cid] = "0"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_on",
            {"entity_id": allow_grid_charging_entity_id},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            str(1 << bit),
            None,
        )

    async def test_turn_off(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        allow_grid_charging_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.storage_mode.cid
        bit = StorageMode.BIT_GRID_CHARGING
        new_data = dict(coordinator.data)
        new_data[cid] = str(1 << bit)

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_off",
            {"entity_id": allow_grid_charging_entity_id},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            str(0),
            None,
        )


class TestGridPeakShavingSwitch:
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        grid_peak_shaving_entity_id: str,
    ):
        state = hass.states.get(grid_peak_shaving_entity_id)
        assert state is not None

    @pytest.mark.parametrize(
        ("value", "expected_is_on"),
        [
            (str((1 << StorageMode.BIT_SELF_USE) | (1 << StorageMode.BIT_PEAK_SHAVING)), True),
            (str(1 << StorageMode.BIT_SELF_USE), False),
            (None, None),
        ],
    )
    async def test_state_from_coordinator(
        self,
        hass: HomeAssistant,
        setup_integration,
        any_inverter: Inverter,
        grid_peak_shaving_entity_id: str,
        value,
        expected_is_on,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.storage_mode.cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(grid_peak_shaving_entity_id)
        assert state.state == "on" if expected_is_on else "off" if expected_is_on is False else "unknown"

    @pytest.mark.parametrize(
        ("storage_mode_value", "expected_available"),
        [
            (str(1 << StorageMode.BIT_SELF_USE), True),
            (str(1 << StorageMode.BIT_FEED_IN_PRIORITY), True),
            (str(1 << StorageMode.BIT_OFF_GRID), False),
            (None, False),
        ],
    )
    async def test_availability(
        self,
        hass: HomeAssistant,
        setup_integration,
        any_inverter: Inverter,
        grid_peak_shaving_entity_id: str,
        storage_mode_value,
        expected_available,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.storage_mode.cid
        new_data = dict(coordinator.data)
        new_data[cid] = storage_mode_value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(grid_peak_shaving_entity_id)
        assert state.state == "unavailable" if not expected_available else state.state != "unavailable"

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        grid_peak_shaving_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.storage_mode.cid
        bit = StorageMode.BIT_PEAK_SHAVING
        new_data = dict(coordinator.data)
        # Start with Self-Use mode (available) without peak shaving
        new_data[cid] = str(1 << StorageMode.BIT_SELF_USE)

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_on",
            {"entity_id": grid_peak_shaving_entity_id},
            blocking=True,
        )

        # Should set Self-Use + Peak Shaving bits
        expected_value = str((1 << StorageMode.BIT_SELF_USE) | (1 << bit))
        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            expected_value,
            None,
        )

    async def test_turn_off(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        grid_peak_shaving_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.storage_mode.cid
        bit = StorageMode.BIT_PEAK_SHAVING
        new_data = dict(coordinator.data)
        # Start with Self-Use + Peak Shaving (available, peak shaving on)
        new_data[cid] = str((1 << StorageMode.BIT_SELF_USE) | (1 << bit))

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_off",
            {"entity_id": grid_peak_shaving_entity_id},
            blocking=True,
        )

        # Should set Self-Use only (peak shaving off)
        expected_value = str(1 << StorageMode.BIT_SELF_USE)
        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            expected_value,
            None,
        )


class TestTimeOfUseSwitch:
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        time_of_use_entity_id: str,
    ):
        state = hass.states.get(time_of_use_entity_id)
        assert state is not None

    @pytest.mark.parametrize(
        ("value", "expected_is_on"),
        [
            (str(1 << StorageMode.BIT_TOU_MODE), True),
            ("0", False),
            (None, None),
        ],
    )
    async def test_state_from_coordinator(
        self,
        hass: HomeAssistant,
        setup_integration,
        any_inverter: Inverter,
        time_of_use_entity_id: str,
        value,
        expected_is_on,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.storage_mode.cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(time_of_use_entity_id)
        assert state.state == "on" if expected_is_on else "off" if expected_is_on is False else "unknown"

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        time_of_use_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.storage_mode.cid
        bit = StorageMode.BIT_TOU_MODE
        new_data = dict(coordinator.data)
        new_data[cid] = "0"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_on",
            {"entity_id": time_of_use_entity_id},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            str(1 << bit),
            None,
        )

    async def test_turn_off(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        time_of_use_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.storage_mode.cid
        bit = StorageMode.BIT_TOU_MODE
        new_data = dict(coordinator.data)
        new_data[cid] = str(1 << bit)

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_off",
            {"entity_id": time_of_use_entity_id},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            str(0),
            None,
        )

    @pytest.mark.parametrize("initial_value", ["not a number", None])
    async def test_turn_on_off_invalid_initial(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        time_of_use_entity_id: str,
        initial_value,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.storage_mode.cid
        new_data = dict(coordinator.data)
        new_data[cid] = initial_value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_on",
            {"entity_id": time_of_use_entity_id},
            blocking=True,
        )
        await hass.services.async_call(
            Platform.SWITCH,
            "turn_off",
            {"entity_id": time_of_use_entity_id},
            blocking=True,
        )

        mock_api_client.control.assert_not_awaited()


class TestMpptScanningSwitch:
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        mppt_scanning_entity_id: str,
    ):
        state = hass.states.get(mppt_scanning_entity_id)
        assert state is not None

    @pytest.mark.parametrize(
        ("value", "expected_is_on"),
        [
            ("1", True),
            ("0", False),
            (None, None),
        ],
    )
    async def test_state_from_coordinator(
        self,
        hass: HomeAssistant,
        setup_integration,
        any_inverter: Inverter,
        mppt_scanning_entity_id: str,
        value,
        expected_is_on,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.mppt_scanning.cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(mppt_scanning_entity_id)
        assert state.state == "on" if expected_is_on else "off" if expected_is_on is False else "unknown"

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        mppt_scanning_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.mppt_scanning.cid
        new_data = dict(coordinator.data)
        new_data[cid] = "0"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_on",
            {"entity_id": mppt_scanning_entity_id},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            "1",
            any_inverter.mppt_scanning.off_value,
        )

    async def test_turn_off(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        mppt_scanning_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.mppt_scanning.cid
        new_data = dict(coordinator.data)
        new_data[cid] = "1"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_off",
            {"entity_id": mppt_scanning_entity_id},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            "0",
            any_inverter.mppt_scanning.on_value,
        )

    async def test_turn_on_when_none(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        mppt_scanning_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.mppt_scanning.cid
        new_data = dict(coordinator.data)
        new_data[cid] = None

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_on",
            {"entity_id": mppt_scanning_entity_id},
            blocking=True,
        )

        mock_api_client.control.assert_not_awaited()

    async def test_turn_off_when_none(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        mppt_scanning_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.mppt_scanning.cid
        new_data = dict(coordinator.data)
        new_data[cid] = None

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_off",
            {"entity_id": mppt_scanning_entity_id},
            blocking=True,
        )

        mock_api_client.control.assert_not_awaited()
