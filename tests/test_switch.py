from typing import TYPE_CHECKING

import pytest
from homeassistant.const import Platform

from custom_components.solis_cloud_control.domain.storage_mode import StorageMode
from tests.helpers import GetEntityId, SetData, assert_control, ensure, get_state

if TYPE_CHECKING:
    from unittest.mock import AsyncMock

    from homeassistant.core import HomeAssistant

    from custom_components.solis_cloud_control.inverters.inverter import Inverter, InverterChargeDischargeSlots


def _slot_data(slots: InverterChargeDischargeSlots) -> dict[int, str]:
    # Valid defaults for every slot CID so that all slot entities are available
    data: dict[int, str] = {}
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
def inverter_on_off_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.SWITCH, "on_off_switch")


@pytest.fixture
def allow_export_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.SWITCH, "allow_export_switch")


@pytest.fixture
def slot1_charge_switch_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.SWITCH, "slot1_charge_switch")


@pytest.fixture
def slot1_discharge_switch_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.SWITCH, "slot1_discharge_switch")


@pytest.fixture
def battery_reserve_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.SWITCH, "battery_reserve")


@pytest.fixture
def allow_grid_charging_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.SWITCH, "allow_grid_charging")


@pytest.fixture
def time_of_use_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.SWITCH, "time_of_use_switch")


@pytest.fixture
def mppt_scanning_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.SWITCH, "mppt_scanning_switch")


@pytest.fixture
def grid_peak_shaving_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.SWITCH, "grid_peak_shaving_switch")


class TestOnOffSwitch:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        inverter_on_off_entity_id: str,
    ) -> None:
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
        set_data: SetData,
        any_inverter: Inverter,
        inverter_on_off_entity_id: str,
        on_value: str,
        off_value: str,
        expected_state: str,
    ) -> None:
        on_cid = ensure(any_inverter.on_off).on_cid
        off_cid = ensure(any_inverter.on_off).off_cid
        await set_data(
            {
                on_cid: on_value,
                off_cid: off_value,
            }
        )

        state = get_state(hass, inverter_on_off_entity_id)
        assert state.state == expected_state

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        inverter_on_off_entity_id: str,
    ) -> None:
        on_cid = ensure(any_inverter.on_off).on_cid
        off_cid = ensure(any_inverter.on_off).off_cid
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

        assert_control(mock_api_client, any_inverter, on_cid, ensure(any_inverter.on_off).on_value)

    async def test_turn_off(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        inverter_on_off_entity_id: str,
    ) -> None:
        on_cid = ensure(any_inverter.on_off).on_cid
        off_cid = ensure(any_inverter.on_off).off_cid
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

        assert_control(mock_api_client, any_inverter, off_cid, ensure(any_inverter.on_off).off_value)


class TestAllowExportSwitch:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        allow_export_entity_id: str,
    ) -> None:
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
        set_data: SetData,
        any_inverter: Inverter,
        allow_export_entity_id: str,
        value: None | str,
        expected_state: str,
    ) -> None:
        cid = ensure(any_inverter.allow_export).cid
        await set_data({cid: value})

        state = get_state(hass, allow_export_entity_id)
        assert state.state == expected_state

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        allow_export_entity_id: str,
    ) -> None:
        cid = ensure(any_inverter.allow_export).cid
        await set_data({cid: "1"})

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_on",
            {"entity_id": allow_export_entity_id},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, "0", ensure(any_inverter.allow_export).off_value)

    async def test_turn_off(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        allow_export_entity_id: str,
    ) -> None:
        cid = ensure(any_inverter.allow_export).cid
        await set_data({cid: "0"})

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_off",
            {"entity_id": allow_export_entity_id},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, "1", ensure(any_inverter.allow_export).on_value)


class TestSlotV2Switch:
    @pytest.mark.usefixtures("setup_integration")
    async def test_charge_entity_registered(
        self,
        hass: HomeAssistant,
        slot1_charge_switch_entity_id: str,
    ) -> None:
        state = hass.states.get(slot1_charge_switch_entity_id)
        assert state is not None

    @pytest.mark.usefixtures("setup_integration")
    async def test_discharge_entity_registered(
        self,
        hass: HomeAssistant,
        slot1_discharge_switch_entity_id: str,
    ) -> None:
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
        set_data: SetData,
        any_inverter: Inverter,
        slot1_charge_switch_entity_id: str,
        value: None | str,
        expected_state: str,
    ) -> None:
        slots = ensure(any_inverter.charge_discharge_slots)
        cid = slots.charge_slot1.switch_cid

        await set_data(
            {
                **_slot_data(slots),
                cid: value,
            }
        )

        state = get_state(hass, slot1_charge_switch_entity_id)
        assert state.state == expected_state

    async def test_charge_turn_on(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        slot1_charge_switch_entity_id: str,
    ) -> None:
        slots = ensure(any_inverter.charge_discharge_slots)
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

        assert_control(mock_api_client, any_inverter, cid, "1", "0")

    async def test_charge_turn_off(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        slot1_charge_switch_entity_id: str,
    ) -> None:
        slots = ensure(any_inverter.charge_discharge_slots)
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

        assert_control(mock_api_client, any_inverter, cid, "0", "1")

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
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        slot1_discharge_switch_entity_id: str,
        service: str,
        initial_value: str,
        new_value: str,
    ) -> None:
        slots = ensure(any_inverter.charge_discharge_slots)
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
        assert_control(
            mock_api_client, any_inverter, cid, new_value, str(int(initial_value) << slots.bit_discharge_slot1)
        )

    async def test_old_value_combines_other_slots(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        slot1_discharge_switch_entity_id: str,
    ) -> None:
        slots = ensure(any_inverter.charge_discharge_slots)
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

        assert_control(
            mock_api_client,
            any_inverter,
            slots.discharge_slot1.switch_cid,
            "1",
            str(1 << slots.bit_charge_slot1 | 1 << slots.bit_discharge_slot2),
        )


class TestBatteryReserveSwitch:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        battery_reserve_entity_id: str,
    ) -> None:
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
        set_data: SetData,
        any_inverter: Inverter,
        battery_reserve_entity_id: str,
        value: None | str,
        expected_state: str,
    ) -> None:
        cid = ensure(any_inverter.storage_mode).cid
        await set_data({cid: value})

        state = get_state(hass, battery_reserve_entity_id)
        assert state.state == expected_state

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        battery_reserve_entity_id: str,
    ) -> None:
        cid = ensure(any_inverter.storage_mode).cid
        bit = StorageMode.BIT_BACKUP_MODE
        await set_data({cid: "0"})

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_on",
            {"entity_id": battery_reserve_entity_id},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, str(1 << bit))

    async def test_turn_off(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        battery_reserve_entity_id: str,
    ) -> None:
        cid = ensure(any_inverter.storage_mode).cid
        bit = StorageMode.BIT_BACKUP_MODE
        await set_data({cid: str(1 << bit)})

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_off",
            {"entity_id": battery_reserve_entity_id},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, str(0))

    async def test_turn_on_off_invalid_initial(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        battery_reserve_entity_id: str,
    ) -> None:
        await set_data({ensure(any_inverter.storage_mode).cid: "not a number"})

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
    ) -> None:
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
        set_data: SetData,
        any_inverter: Inverter,
        allow_grid_charging_entity_id: str,
        value: None | str,
        expected_state: str,
    ) -> None:
        cid = ensure(any_inverter.storage_mode).cid
        await set_data({cid: value})

        state = get_state(hass, allow_grid_charging_entity_id)
        assert state.state == expected_state

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        allow_grid_charging_entity_id: str,
    ) -> None:
        cid = ensure(any_inverter.storage_mode).cid
        bit = StorageMode.BIT_GRID_CHARGING
        await set_data({cid: "0"})

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_on",
            {"entity_id": allow_grid_charging_entity_id},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, str(1 << bit))

    async def test_turn_off(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        allow_grid_charging_entity_id: str,
    ) -> None:
        cid = ensure(any_inverter.storage_mode).cid
        bit = StorageMode.BIT_GRID_CHARGING
        await set_data({cid: str(1 << bit)})

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_off",
            {"entity_id": allow_grid_charging_entity_id},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, str(0))

    async def test_turn_on_off_invalid_initial(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        allow_grid_charging_entity_id: str,
    ) -> None:
        await set_data({ensure(any_inverter.storage_mode).cid: "not a number"})

        for service in ("turn_on", "turn_off"):
            await hass.services.async_call(
                Platform.SWITCH,
                service,
                {"entity_id": allow_grid_charging_entity_id},
                blocking=True,
            )

        mock_api_client.control.assert_not_awaited()


class TestTimeOfUseSwitch:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        time_of_use_entity_id: str,
    ) -> None:
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
        set_data: SetData,
        any_inverter: Inverter,
        time_of_use_entity_id: str,
        value: None | str,
        expected_state: str,
    ) -> None:
        cid = ensure(any_inverter.storage_mode).cid
        await set_data({cid: value})

        state = get_state(hass, time_of_use_entity_id)
        assert state.state == expected_state

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        time_of_use_entity_id: str,
    ) -> None:
        cid = ensure(any_inverter.storage_mode).cid
        bit = StorageMode.BIT_TOU_MODE
        await set_data({cid: "0"})

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_on",
            {"entity_id": time_of_use_entity_id},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, str(1 << bit))

    async def test_turn_off(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        time_of_use_entity_id: str,
    ) -> None:
        cid = ensure(any_inverter.storage_mode).cid
        bit = StorageMode.BIT_TOU_MODE
        await set_data({cid: str(1 << bit)})

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_off",
            {"entity_id": time_of_use_entity_id},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, str(0))

    async def test_turn_on_off_invalid_initial(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        time_of_use_entity_id: str,
    ) -> None:
        await set_data({ensure(any_inverter.storage_mode).cid: "not a number"})

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
    ) -> None:
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
        set_data: SetData,
        any_inverter: Inverter,
        mppt_scanning_entity_id: str,
        value: None | str,
        expected_state: str,
    ) -> None:
        cid = ensure(any_inverter.mppt_scanning).cid
        await set_data({cid: value})

        state = get_state(hass, mppt_scanning_entity_id)
        assert state.state == expected_state

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        mppt_scanning_entity_id: str,
    ) -> None:
        cid = ensure(any_inverter.mppt_scanning).cid
        await set_data({cid: "0"})

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_on",
            {"entity_id": mppt_scanning_entity_id},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, "1", ensure(any_inverter.mppt_scanning).off_value)

    async def test_turn_off(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        mppt_scanning_entity_id: str,
    ) -> None:
        cid = ensure(any_inverter.mppt_scanning).cid
        await set_data({cid: "1"})

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_off",
            {"entity_id": mppt_scanning_entity_id},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, "0", ensure(any_inverter.mppt_scanning).on_value)


class TestGridPeakShavingSwitch:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        grid_peak_shaving_entity_id: str,
    ) -> None:
        state = hass.states.get(grid_peak_shaving_entity_id)
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
        set_data: SetData,
        any_inverter: Inverter,
        grid_peak_shaving_entity_id: str,
        value: None | str,
        expected_state: str,
    ) -> None:
        cid = ensure(any_inverter.grid_peak_shaving).cid
        await set_data({cid: value})

        state = get_state(hass, grid_peak_shaving_entity_id)
        assert state.state == expected_state

    async def test_turn_on(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        grid_peak_shaving_entity_id: str,
    ) -> None:
        cid = ensure(any_inverter.grid_peak_shaving).cid
        await set_data({cid: "0"})

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_on",
            {"entity_id": grid_peak_shaving_entity_id},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, "1", "0")

    async def test_turn_off(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        grid_peak_shaving_entity_id: str,
    ) -> None:
        cid = ensure(any_inverter.grid_peak_shaving).cid
        await set_data({cid: "1"})

        await hass.services.async_call(
            Platform.SWITCH,
            "turn_off",
            {"entity_id": grid_peak_shaving_entity_id},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, "0", "1")
