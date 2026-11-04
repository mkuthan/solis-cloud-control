import pytest
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from custom_components.solis_cloud_control.inverters.inverter import Inverter
from custom_components.solis_cloud_control.text import TimeSlotV1Text, TimeSlotV2Text


@pytest.fixture
def slot1_charge_v1_entity_id(any_inverter: Inverter) -> str:
    # V1 entities created FIRST, get base entity_id (no suffix)
    return f"text.inverter_control_{any_inverter.info.serial_number}_slot1_charge_time"


@pytest.fixture
def slot1_discharge_v1_entity_id(any_inverter: Inverter) -> str:
    return f"text.inverter_control_{any_inverter.info.serial_number}_slot1_discharge_time"


@pytest.fixture
def slot1_charge_v2_entity_id(any_inverter: Inverter) -> str:
    # V2 entities created SECOND, get _2 suffix
    return f"text.inverter_control_{any_inverter.info.serial_number}_slot1_charge_time_2"


@pytest.fixture
def slot1_discharge_v2_entity_id(any_inverter: Inverter) -> str:
    return f"text.inverter_control_{any_inverter.info.serial_number}_slot1_discharge_time_2"


class TestTimeSlotV1Text:
    VARIANT1_VALUE = "0,0,09:00,10:00,11:00,12:00,50,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00"
    VARIANT2_VALUE = "0,0,09:00-10:00,11:00-12:00,50,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00"

    async def test_charge_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        slot1_charge_v1_entity_id: str,
    ) -> None:
        state = hass.states.get(slot1_charge_v1_entity_id)
        assert state is not None
        assert state.attributes.get("min") == TimeSlotV1Text._TEXT_LENGTH
        assert state.attributes.get("max") == TimeSlotV1Text._TEXT_LENGTH
        assert state.attributes.get("pattern") == TimeSlotV1Text._TEXT_PATTERN

    async def test_discharge_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        slot1_discharge_v1_entity_id: str,
    ) -> None:
        state = hass.states.get(slot1_discharge_v1_entity_id)
        assert state is not None
        assert state.attributes.get("min") == TimeSlotV1Text._TEXT_LENGTH
        assert state.attributes.get("max") == TimeSlotV1Text._TEXT_LENGTH
        assert state.attributes.get("pattern") == TimeSlotV1Text._TEXT_PATTERN

    @pytest.mark.parametrize("value", [VARIANT1_VALUE, VARIANT2_VALUE])
    async def test_charge_slot_native_value(
        self,
        hass: HomeAssistant,
        setup_integration,
        any_inverter: Inverter,
        slot1_charge_v1_entity_id: str,
        value,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.charge_discharge_settings.cid

        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(slot1_charge_v1_entity_id)
        assert state.state == "09:00-10:00"

    @pytest.mark.parametrize("value", [VARIANT1_VALUE, VARIANT2_VALUE])
    async def test_discharge_slot_native_value(
        self,
        hass: HomeAssistant,
        setup_integration,
        any_inverter: Inverter,
        slot1_discharge_v1_entity_id: str,
        value,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.charge_discharge_settings.cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(slot1_discharge_v1_entity_id)
        assert state.state == "11:00-12:00"

    async def test_charge_slot_native_value_no_data(
        self,
        hass: HomeAssistant,
        setup_integration,
        any_inverter: Inverter,
        slot1_charge_v1_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.charge_discharge_settings.cid
        new_data = dict(coordinator.data)
        new_data[cid] = None

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(slot1_charge_v1_entity_id)
        assert state.state in ("unavailable", "unknown")

    @pytest.mark.parametrize(
        ("initial_value", "expected_value"),
        [
            (
                VARIANT1_VALUE,
                "0,0,23:00,23:59,11:00,12:00,50,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00",
            ),
            (
                VARIANT2_VALUE,
                "0,0,23:00-23:59,11:00-12:00,50,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00",
            ),
        ],
    )
    async def test_async_set_value_charge_slot(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        slot1_charge_v1_entity_id: str,
        initial_value,
        expected_value,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.charge_discharge_settings.cid
        new_data = dict(coordinator.data)
        new_data[cid] = initial_value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.TEXT,
            "set_value",
            {"entity_id": slot1_charge_v1_entity_id, "value": "23:00-23:59"},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            expected_value,
            None,
        )

    @pytest.mark.parametrize(
        ("initial_value", "expected_value"),
        [
            (
                VARIANT1_VALUE,
                "0,0,09:00,10:00,23:00,23:59,50,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00",
            ),
            (
                VARIANT2_VALUE,
                "0,0,09:00-10:00,23:00-23:59,50,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00",
            ),
        ],
    )
    async def test_async_set_value_discharge_slot(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        slot1_discharge_v1_entity_id: str,
        initial_value,
        expected_value,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.charge_discharge_settings.cid
        new_data = dict(coordinator.data)
        new_data[cid] = initial_value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.TEXT,
            "set_value",
            {"entity_id": slot1_discharge_v1_entity_id, "value": "23:00-23:59"},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            expected_value,
            None,
        )

    @pytest.mark.parametrize("initial_value", ["invalid format", None])
    async def test_async_set_value_invalid_initial(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        slot1_charge_v1_entity_id: str,
        initial_value,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.charge_discharge_settings.cid
        new_data = dict(coordinator.data)
        new_data[cid] = initial_value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.TEXT,
            "set_value",
            {"entity_id": slot1_charge_v1_entity_id, "value": "23:00-23:59"},
            blocking=True,
        )

        mock_api_client.control.assert_not_awaited()


class TestTimeSlotV2Text:
    async def test_charge_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        slot1_charge_v2_entity_id: str,
    ) -> None:
        state = hass.states.get(slot1_charge_v2_entity_id)
        assert state is not None
        assert state.attributes.get("min") == TimeSlotV2Text._TEXT_LENGTH
        assert state.attributes.get("max") == TimeSlotV2Text._TEXT_LENGTH
        assert state.attributes.get("pattern") == TimeSlotV2Text._TEXT_PATTERN

    async def test_discharge_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        slot1_discharge_v2_entity_id: str,
    ) -> None:
        state = hass.states.get(slot1_discharge_v2_entity_id)
        assert state is not None
        assert state.attributes.get("min") == TimeSlotV2Text._TEXT_LENGTH
        assert state.attributes.get("max") == TimeSlotV2Text._TEXT_LENGTH
        assert state.attributes.get("pattern") == TimeSlotV2Text._TEXT_PATTERN

    async def test_charge_slot_native_value(
        self,
        hass: HomeAssistant,
        setup_integration,
        any_inverter: Inverter,
        slot1_charge_v2_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.charge_discharge_slots.charge_slot1.time_cid
        new_data = dict(coordinator.data)
        new_data[cid] = "10:00-12:00"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(slot1_charge_v2_entity_id)
        assert state.state == "10:00-12:00"

    async def test_discharge_slot_native_value(
        self,
        hass: HomeAssistant,
        setup_integration,
        any_inverter: Inverter,
        slot1_discharge_v2_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.charge_discharge_slots.discharge_slot1.time_cid
        new_data = dict(coordinator.data)
        new_data[cid] = "14:00-16:00"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(slot1_discharge_v2_entity_id)
        assert state.state == "14:00-16:00"

    async def test_charge_slot_native_value_no_data(
        self,
        hass: HomeAssistant,
        setup_integration,
        any_inverter: Inverter,
        slot1_charge_v2_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.charge_discharge_slots.charge_slot1.time_cid
        new_data = dict(coordinator.data)
        new_data[cid] = None

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(slot1_charge_v2_entity_id)
        assert state.state in ("unavailable", "unknown")

    async def test_async_set_value_charge_slot(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        slot1_charge_v2_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.charge_discharge_slots.charge_slot1.time_cid
        new_data = dict(coordinator.data)
        new_data[cid] = "10:00-12:00"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.TEXT,
            "set_value",
            {"entity_id": slot1_charge_v2_entity_id, "value": "09:00-17:00"},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            "09:00-17:00",
            None,
        )

    async def test_async_set_value_discharge_slot(
        self,
        hass: HomeAssistant,
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        slot1_discharge_v2_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.charge_discharge_slots.discharge_slot1.time_cid
        new_data = dict(coordinator.data)
        new_data[cid] = "14:00-16:00"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.TEXT,
            "set_value",
            {"entity_id": slot1_discharge_v2_entity_id, "value": "18:00-22:00"},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            "18:00-22:00",
            None,
        )
