import pytest
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from custom_components.solis_cloud_control.domain.storage_mode import StorageMode
from custom_components.solis_cloud_control.inverters.inverter import Inverter


def _slot_data(slots) -> dict:
    # Valid defaults for every slot CID so that all slot entities are available
    data = {}
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
        data[slot.switch_cid] = "0"
        data[slot.time_cid] = "00:00-00:00"
        data[slot.current_cid] = "0"
        data[slot.soc_cid] = "0"
    return data


@pytest.fixture
def inverter_on_off_entity_id(get_entity_id) -> str:
    return get_entity_id(Platform.SWITCH, "on_off_switch")


@pytest.fixture
def allow_export_entity_id(get_entity_id) -> str:
    return get_entity_id(Platform.SWITCH, "allow_export_switch")


@pytest.fixture
def slot1_charge_switch_entity_id(get_entity_id) -> str:
    return get_entity_id(Platform.SWITCH, "slot1_charge_switch")


@pytest.fixture
def slot1_discharge_switch_entity_id(get_entity_id) -> str:
    return get_entity_id(Platform.SWITCH, "slot1_discharge_switch")


@pytest.fixture
def battery_reserve_entity_id(get_entity_id) -> str:
    return get_entity_id(Platform.SWITCH, "battery_reserve")


@pytest.fixture
def allow_grid_charging_entity_id(get_entity_id) -> str:
    return get_entity_id(Platform.SWITCH, "allow_grid_charging")


@pytest.fixture
def grid_peak_shaving_entity_id(get_entity_id) -> str:
    return get_entity_id(Platform.SWITCH, "grid_peak_shaving")


@pytest.fixture
def time_of_use_entity_id(get_entity_id) -> str:
    return get_entity_id(Platform.SWITCH, "time_of_use_switch")


@pytest.fixture
def mppt_scanning_entity_id(get_entity_id) -> str:
    return get_entity_id(Platform.SWITCH, "mppt_scanning_switch")


class TestOnOffSwitch:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        inverter_on_off_entity_id: str,
    ):
        state = hass.states.get(inverter_on_off_entity_id)
        assert state is not None

    @pytest.mark.parametrize(
        ("on_value", "off_value", "expected_state"),
        [
            ("190", "190", "on"),
            ("222", "222", "off"),
            ("190", "222", "unknown"),
            ("0", "0", "unknown"),
        ],
    )
    async def test_state_from_coordinator(
        self,
        hass: HomeAssistant,
        set_data,
        any_inverter: Inverter,
        inverter_on_off_entity_id: str,
        on_value,
        off_value,
        expected_state,
    ):
        on_cid = any_inverter.on_off.on_cid
        off_cid = any_inverter.on_off.off_cid
        await set_data(
            {
                on_cid: on_value,
                off_cid: off_value,
            }
        )

        state = hass.states.get(inverter_on_off_entity_id)
        assert state.state == expected_state

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        inverter_on_off_entity_id: str,
    ):
        on_cid = any_inverter.on_off.on_cid
        off_cid = any_inverter.on_off.off_cid
        await set_data(
            {
                on_cid: "222",
                off_cid: "222",
            }
        )

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
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        inverter_on_off_entity_id: str,
    ):
        on_cid = any_inverter.on_off.on_cid
        off_cid = any_inverter.on_off.off_cid
        await set_data(
            {
                on_cid: "190",
                off_cid: "190",
            }
        )

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
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        allow_export_entity_id: str,
    ):
        state = hass.states.get(allow_export_entity_id)
        assert state is not None

    @pytest.mark.parametrize(
        ("value", "expected_state"),
        [
            ("0", "on"),
            ("1", "off"),
            (None, "unavailable"),
        ],
    )
    async def test_state_from_coordinator(
        self,
        hass: HomeAssistant,
        set_data,
        any_inverter: Inverter,
        allow_export_entity_id: str,
        value,
        expected_state,
    ):
        cid = any_inverter.allow_export.cid
        storage_cid = any_inverter.storage_mode.cid
        await set_data(
            {
                cid: value,
                storage_cid: str(1 << StorageMode.BIT_SELF_USE),
            }
        )

        state = hass.states.get(allow_export_entity_id)
        assert state.state == expected_state

    @pytest.mark.parametrize(
        ("storage_mode_value", "expected_state"),
        [
            (str(1 << StorageMode.BIT_SELF_USE), "on"),
            (str(1 << StorageMode.BIT_FEED_IN_PRIORITY), "unavailable"),
            (str(1 << StorageMode.BIT_OFF_GRID), "unavailable"),
            (None, "unavailable"),
        ],
    )
    async def test_availability(
        self,
        hass: HomeAssistant,
        set_data,
        any_inverter: Inverter,
        allow_export_entity_id: str,
        storage_mode_value,
        expected_state,
    ):
        storage_cid = any_inverter.storage_mode.cid
        export_cid = any_inverter.allow_export.cid
        await set_data(
            {
                storage_cid: storage_mode_value,
                export_cid: "0",
            }
        )

        state = hass.states.get(allow_export_entity_id)
        assert state.state == expected_state

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        allow_export_entity_id: str,
    ):
        cid = any_inverter.allow_export.cid
        storage_cid = any_inverter.storage_mode.cid
        await set_data(
            {
                cid: "1",
                storage_cid: str(1 << StorageMode.BIT_SELF_USE),
            }
        )

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
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        allow_export_entity_id: str,
    ):
        cid = any_inverter.allow_export.cid
        storage_cid = any_inverter.storage_mode.cid
        await set_data(
            {
                cid: "0",
                storage_cid: str(1 << StorageMode.BIT_SELF_USE),
            }
        )

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


class TestSlotV2Switch:
    @pytest.mark.usefixtures("setup_integration")
    async def test_charge_entity_registered(
        self,
        hass: HomeAssistant,
        slot1_charge_switch_entity_id: str,
    ):
        state = hass.states.get(slot1_charge_switch_entity_id)
        assert state is not None

    @pytest.mark.usefixtures("setup_integration")
    async def test_discharge_entity_registered(
        self,
        hass: HomeAssistant,
        slot1_discharge_switch_entity_id: str,
    ):
        state = hass.states.get(slot1_discharge_switch_entity_id)
        assert state is not None

    @pytest.mark.parametrize(
        ("value", "expected_state"),
        [
            ("1", "on"),
            ("0", "off"),
            (None, "unavailable"),
        ],
    )
    async def test_charge_state_from_coordinator(
        self,
        hass: HomeAssistant,
        set_data,
        any_inverter: Inverter,
        slot1_charge_switch_entity_id: str,
        value,
        expected_state,
    ):
        slots = any_inverter.charge_discharge_slots
        cid = slots.charge_slot1.switch_cid

        await set_data(
            {
                **_slot_data(slots),
                cid: value,
            }
        )

        state = hass.states.get(slot1_charge_switch_entity_id)
        assert state.state == expected_state

    async def test_charge_turn_on(
        self,
        hass: HomeAssistant,
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        slot1_charge_switch_entity_id: str,
    ):
        slots = any_inverter.charge_discharge_slots
        cid = slots.charge_slot1.switch_cid

        await set_data(
            {
                **_slot_data(slots),
                cid: "0",
            }
        )

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
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        slot1_charge_switch_entity_id: str,
    ):
        slots = any_inverter.charge_discharge_slots
        cid = slots.charge_slot1.switch_cid

        await set_data(
            {
                **_slot_data(slots),
                cid: "1",
            }
        )

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

    @pytest.mark.parametrize(
        ("service", "initial_value", "new_value"),
        [
            ("turn_on", "0", "1"),
            ("turn_off", "1", "0"),
        ],
    )
    async def test_discharge_turn_on_off(
        self,
        hass: HomeAssistant,
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        slot1_discharge_switch_entity_id: str,
        service: str,
        initial_value: str,
        new_value: str,
    ):
        slots = any_inverter.charge_discharge_slots
        cid = slots.discharge_slot1.switch_cid
        await set_data(
            {
                **_slot_data(slots),
                cid: initial_value,
            }
        )

        await hass.services.async_call(
            Platform.SWITCH,
            service,
            {"entity_id": slot1_discharge_switch_entity_id},
            blocking=True,
        )

        # old_value is a bitfield of all slot switches, so it must carry the target slot's own bit
        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            new_value,
            str(int(initial_value) << slots.bit_discharge_slot1),
        )

    async def test_old_value_combines_other_slots(
        self,
        hass: HomeAssistant,
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        slot1_discharge_switch_entity_id: str,
    ):
        slots = any_inverter.charge_discharge_slots
        await set_data(
            {
                **_slot_data(slots),
                slots.charge_slot1.switch_cid: "1",
                slots.discharge_slot2.switch_cid: "1",
            }
        )

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_on",
            {"entity_id": slot1_discharge_switch_entity_id},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            slots.discharge_slot1.switch_cid,
            "1",
            str((1 << slots.bit_charge_slot1) | (1 << slots.bit_discharge_slot2)),
        )


class TestBatteryReserveSwitch:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        battery_reserve_entity_id: str,
    ):
        state = hass.states.get(battery_reserve_entity_id)
        assert state is not None

    @pytest.mark.parametrize(
        ("value", "expected_state"),
        [
            (str(1 << StorageMode.BIT_BACKUP_MODE), "on"),
            ("0", "off"),
            (None, "unavailable"),
            ("not a number", "unknown"),
        ],
    )
    async def test_state_from_coordinator(
        self,
        hass: HomeAssistant,
        set_data,
        any_inverter: Inverter,
        battery_reserve_entity_id: str,
        value,
        expected_state,
    ):
        cid = any_inverter.storage_mode.cid
        await set_data({cid: value})

        state = hass.states.get(battery_reserve_entity_id)
        assert state.state == expected_state

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        battery_reserve_entity_id: str,
    ):
        cid = any_inverter.storage_mode.cid
        bit = StorageMode.BIT_BACKUP_MODE
        await set_data({cid: "0"})

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
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        battery_reserve_entity_id: str,
    ):
        cid = any_inverter.storage_mode.cid
        bit = StorageMode.BIT_BACKUP_MODE
        await set_data({cid: str(1 << bit)})

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

    async def test_turn_on_off_invalid_initial(
        self,
        hass: HomeAssistant,
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        battery_reserve_entity_id: str,
    ):
        await set_data({any_inverter.storage_mode.cid: "not a number"})

        for service in ("turn_on", "turn_off"):
            await hass.services.async_call(
                Platform.SWITCH,
                service,
                {"entity_id": battery_reserve_entity_id},
                blocking=True,
            )

        mock_api_client.control.assert_not_awaited()


class TestAllowGridChargingSwitch:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        allow_grid_charging_entity_id: str,
    ):
        state = hass.states.get(allow_grid_charging_entity_id)
        assert state is not None

    @pytest.mark.parametrize(
        ("value", "expected_state"),
        [
            (str(1 << StorageMode.BIT_GRID_CHARGING), "on"),
            ("0", "off"),
            (None, "unavailable"),
        ],
    )
    async def test_state_from_coordinator(
        self,
        hass: HomeAssistant,
        set_data,
        any_inverter: Inverter,
        allow_grid_charging_entity_id: str,
        value,
        expected_state,
    ):
        cid = any_inverter.storage_mode.cid
        await set_data({cid: value})

        state = hass.states.get(allow_grid_charging_entity_id)
        assert state.state == expected_state

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        allow_grid_charging_entity_id: str,
    ):
        cid = any_inverter.storage_mode.cid
        bit = StorageMode.BIT_GRID_CHARGING
        await set_data({cid: "0"})

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
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        allow_grid_charging_entity_id: str,
    ):
        cid = any_inverter.storage_mode.cid
        bit = StorageMode.BIT_GRID_CHARGING
        await set_data({cid: str(1 << bit)})

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

    async def test_turn_on_off_invalid_initial(
        self,
        hass: HomeAssistant,
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        allow_grid_charging_entity_id: str,
    ):
        await set_data({any_inverter.storage_mode.cid: "not a number"})

        for service in ("turn_on", "turn_off"):
            await hass.services.async_call(
                Platform.SWITCH,
                service,
                {"entity_id": allow_grid_charging_entity_id},
                blocking=True,
            )

        mock_api_client.control.assert_not_awaited()


class TestGridPeakShavingSwitch:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        grid_peak_shaving_entity_id: str,
    ):
        state = hass.states.get(grid_peak_shaving_entity_id)
        assert state is not None

    @pytest.mark.parametrize(
        ("value", "expected_state"),
        [
            (str((1 << StorageMode.BIT_SELF_USE) | (1 << StorageMode.BIT_PEAK_SHAVING)), "on"),
            (str(1 << StorageMode.BIT_SELF_USE), "off"),
            (None, "unavailable"),
        ],
    )
    async def test_state_from_coordinator(
        self,
        hass: HomeAssistant,
        set_data,
        any_inverter: Inverter,
        grid_peak_shaving_entity_id: str,
        value,
        expected_state,
    ):
        cid = any_inverter.storage_mode.cid
        await set_data({cid: value})

        state = hass.states.get(grid_peak_shaving_entity_id)
        assert state.state == expected_state

    @pytest.mark.parametrize(
        ("storage_mode_value", "expected_state"),
        [
            (str(1 << StorageMode.BIT_SELF_USE), "off"),
            (str(1 << StorageMode.BIT_FEED_IN_PRIORITY), "off"),
            (str(1 << StorageMode.BIT_OFF_GRID), "unavailable"),
            ("not a number", "unavailable"),
            (None, "unavailable"),
        ],
    )
    async def test_availability(
        self,
        hass: HomeAssistant,
        set_data,
        any_inverter: Inverter,
        grid_peak_shaving_entity_id: str,
        storage_mode_value,
        expected_state,
    ):
        cid = any_inverter.storage_mode.cid
        await set_data({cid: storage_mode_value})

        state = hass.states.get(grid_peak_shaving_entity_id)
        assert state.state == expected_state

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        grid_peak_shaving_entity_id: str,
    ):
        cid = any_inverter.storage_mode.cid
        bit = StorageMode.BIT_PEAK_SHAVING
        # Start with Self-Use mode (available) without peak shaving
        await set_data({cid: str(1 << StorageMode.BIT_SELF_USE)})

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
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        grid_peak_shaving_entity_id: str,
    ):
        cid = any_inverter.storage_mode.cid
        bit = StorageMode.BIT_PEAK_SHAVING
        # Start with Self-Use + Peak Shaving (available, peak shaving on)
        await set_data({cid: str((1 << StorageMode.BIT_SELF_USE) | (1 << bit))})

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
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        time_of_use_entity_id: str,
    ):
        state = hass.states.get(time_of_use_entity_id)
        assert state is not None

    @pytest.mark.parametrize(
        ("value", "expected_state"),
        [
            (str(1 << StorageMode.BIT_TOU_MODE), "on"),
            ("0", "off"),
            (None, "unavailable"),
        ],
    )
    async def test_state_from_coordinator(
        self,
        hass: HomeAssistant,
        set_data,
        any_inverter: Inverter,
        time_of_use_entity_id: str,
        value,
        expected_state,
    ):
        cid = any_inverter.storage_mode.cid
        await set_data({cid: value})

        state = hass.states.get(time_of_use_entity_id)
        assert state.state == expected_state

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        time_of_use_entity_id: str,
    ):
        cid = any_inverter.storage_mode.cid
        bit = StorageMode.BIT_TOU_MODE
        await set_data({cid: "0"})

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
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        time_of_use_entity_id: str,
    ):
        cid = any_inverter.storage_mode.cid
        bit = StorageMode.BIT_TOU_MODE
        await set_data({cid: str(1 << bit)})

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

    async def test_turn_on_off_invalid_initial(
        self,
        hass: HomeAssistant,
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        time_of_use_entity_id: str,
    ):
        await set_data({any_inverter.storage_mode.cid: "not a number"})

        for service in ("turn_on", "turn_off"):
            await hass.services.async_call(
                Platform.SWITCH,
                service,
                {"entity_id": time_of_use_entity_id},
                blocking=True,
            )

        mock_api_client.control.assert_not_awaited()


class TestMpptScanningSwitch:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        mppt_scanning_entity_id: str,
    ):
        state = hass.states.get(mppt_scanning_entity_id)
        assert state is not None

    @pytest.mark.parametrize(
        ("value", "expected_state"),
        [
            ("1", "on"),
            ("0", "off"),
            (None, "unavailable"),
        ],
    )
    async def test_state_from_coordinator(
        self,
        hass: HomeAssistant,
        set_data,
        any_inverter: Inverter,
        mppt_scanning_entity_id: str,
        value,
        expected_state,
    ):
        cid = any_inverter.mppt_scanning.cid
        await set_data({cid: value})

        state = hass.states.get(mppt_scanning_entity_id)
        assert state.state == expected_state

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        mppt_scanning_entity_id: str,
    ):
        cid = any_inverter.mppt_scanning.cid
        await set_data({cid: "0"})

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
        set_data,
        mock_api_client,
        any_inverter: Inverter,
        mppt_scanning_entity_id: str,
    ):
        cid = any_inverter.mppt_scanning.cid
        await set_data({cid: "1"})

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
