from dataclasses import replace
from typing import TYPE_CHECKING

import pytest
from homeassistant.const import Platform

from custom_components.solis_cloud_control.inverters.inverter import (
    Inverter,
    InverterBatteryForceChargeSOC,
    InverterBatteryMaxChargeCurrent,
    InverterChargeDischargeSettings,
    InverterChargeDischargeSlot,
    InverterExportCalibration,
    InverterGridPeakShavingPower,
    InverterMaxExportPower,
    InverterMaxOutputPower,
    InverterMpptScanInterval,
    InverterPeakShavingBaselineSOC,
    InverterPeakShavingMaxUsableGridPower,
    InverterPowerLimit,
)
from tests.helpers import GetEntityId, SetData, assert_control, ensure, get_state

if TYPE_CHECKING:
    from collections.abc import Callable
    from unittest.mock import AsyncMock

    from homeassistant.core import HomeAssistant


@pytest.fixture
def slot1_charge_current_v1_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.NUMBER, "slot1_charge_current_v1")


@pytest.fixture
def slot1_discharge_current_v1_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.NUMBER, "slot1_discharge_current_v1")


@pytest.fixture
def slot1_charge_current_v2_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.NUMBER, "slot1_charge_current")


@pytest.fixture
def slot1_discharge_current_v2_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.NUMBER, "slot1_discharge_current")


@pytest.fixture
def slot1_charge_soc_v2_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.NUMBER, "slot1_charge_soc")


@pytest.fixture
def slot1_discharge_soc_v2_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.NUMBER, "slot1_discharge_soc")


@pytest.fixture
def max_output_power_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.NUMBER, "max_output_power")


@pytest.fixture
def max_export_power_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.NUMBER, "max_export_power")


@pytest.fixture
def export_calibration_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.NUMBER, "export_calibration")


@pytest.fixture
def power_limit_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.NUMBER, "power_limit")


@pytest.fixture
def battery_force_charge_soc_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.NUMBER, "battery_force_charge_soc")


@pytest.fixture
def battery_max_charge_current_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.NUMBER, "battery_max_charge_current")


@pytest.fixture
def mppt_scan_interval_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.NUMBER, "mppt_scan_interval")


@pytest.fixture
def peak_shaving_max_usable_grid_power_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.NUMBER, "peak_shaving_max_usable_grid_power")


@pytest.fixture
def peak_shaving_baseline_soc_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.NUMBER, "peak_shaving_baseline_soc")


@pytest.fixture
def grid_peak_shaving_power_entity_id(get_entity_id: GetEntityId) -> str:
    return get_entity_id(Platform.NUMBER, "grid_peak_shaving_power")


class TestBatteryCurrentV1:
    VARIANT1_VALUE = "50,0,09:00,10:00,11:00,12:00,0,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00"
    VARIANT2_VALUE = "50,0,09:00-10:00,11:00-12:00,0,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00"

    @pytest.mark.usefixtures("setup_integration")
    async def test_charge_entity_registered(
        self,
        hass: HomeAssistant,
        slot1_charge_current_v1_entity_id: str,
    ) -> None:
        state = hass.states.get(slot1_charge_current_v1_entity_id)
        assert state is not None
        assert state.attributes.get("min") == InverterChargeDischargeSettings.current_min_value
        assert state.attributes.get("max") == InverterChargeDischargeSettings.current_max_value
        assert state.attributes.get("step") == InverterChargeDischargeSettings.current_step
        assert state.attributes.get("unit_of_measurement") == "A"

    @pytest.mark.usefixtures("setup_integration")
    async def test_discharge_entity_registered(
        self,
        hass: HomeAssistant,
        slot1_discharge_current_v1_entity_id: str,
    ) -> None:
        state = hass.states.get(slot1_discharge_current_v1_entity_id)
        assert state is not None
        assert state.attributes.get("min") == InverterChargeDischargeSettings.current_min_value
        assert state.attributes.get("max") == InverterChargeDischargeSettings.current_max_value
        assert state.attributes.get("step") == InverterChargeDischargeSettings.current_step
        assert state.attributes.get("unit_of_measurement") == "A"

    @pytest.mark.parametrize("value", [VARIANT1_VALUE, VARIANT2_VALUE])
    async def test_charge_current_native_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        slot1_charge_current_v1_entity_id: str,
        value: str,
    ) -> None:
        cid = ensure(any_inverter.charge_discharge_settings).cid
        await set_data({cid: value})

        state = get_state(hass, slot1_charge_current_v1_entity_id)
        assert state.state == "50.0"

    @pytest.mark.parametrize("value", [VARIANT1_VALUE, VARIANT2_VALUE])
    async def test_discharge_current_native_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        slot1_discharge_current_v1_entity_id: str,
        value: str,
    ) -> None:
        cid = ensure(any_inverter.charge_discharge_settings).cid
        await set_data({cid: value})

        state = get_state(hass, slot1_discharge_current_v1_entity_id)
        assert state.state == "0.0"

    async def test_charge_current_native_value_no_data(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        slot1_charge_current_v1_entity_id: str,
    ) -> None:
        cid = ensure(any_inverter.charge_discharge_settings).cid
        await set_data({cid: None})

        state = get_state(hass, slot1_charge_current_v1_entity_id)
        assert state.state == "unavailable"

    @pytest.mark.parametrize(
        ("initial_value", "expected_value"),
        [
            (
                VARIANT1_VALUE,
                "99,0,09:00,10:00,11:00,12:00,0,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00",
            ),
            (
                VARIANT2_VALUE,
                "99,0,09:00-10:00,11:00-12:00,0,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00",
            ),
        ],
    )
    async def test_async_set_value_charge_current(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        slot1_charge_current_v1_entity_id: str,
        initial_value: str,
        expected_value: str,
    ) -> None:
        cid = ensure(any_inverter.charge_discharge_settings).cid
        await set_data({cid: initial_value})

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": slot1_charge_current_v1_entity_id, "value": 99},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, expected_value)

    @pytest.mark.parametrize(
        ("initial_value", "expected_value"),
        [
            (
                VARIANT1_VALUE,
                "50,99,09:00,10:00,11:00,12:00,0,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00",
            ),
            (
                VARIANT2_VALUE,
                "50,99,09:00-10:00,11:00-12:00,0,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00",
            ),
        ],
    )
    async def test_async_set_value_discharge_current(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        slot1_discharge_current_v1_entity_id: str,
        initial_value: str,
        expected_value: str,
    ) -> None:
        cid = ensure(any_inverter.charge_discharge_settings).cid
        await set_data({cid: initial_value})

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": slot1_discharge_current_v1_entity_id, "value": 99},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, expected_value)

    @pytest.mark.parametrize("initial_value", ["invalid format", None])
    async def test_async_set_value_invalid_initial(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        slot1_charge_current_v1_entity_id: str,
        initial_value: None | str,
    ) -> None:
        cid = ensure(any_inverter.charge_discharge_settings).cid
        await set_data({cid: initial_value})

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": slot1_charge_current_v1_entity_id, "value": 99},
            blocking=True,
        )

        mock_api_client.control.assert_not_awaited()


class TestBatteryCurrentV2:
    @pytest.mark.usefixtures("setup_integration")
    async def test_charge_entity_registered(
        self,
        hass: HomeAssistant,
        slot1_charge_current_v2_entity_id: str,
    ) -> None:
        state = hass.states.get(slot1_charge_current_v2_entity_id)
        assert state is not None
        assert state.attributes.get("min") == InverterChargeDischargeSlot.current_min_value
        assert state.attributes.get("max") == InverterChargeDischargeSlot.current_max_value
        assert state.attributes.get("step") == InverterChargeDischargeSlot.current_step
        assert state.attributes.get("unit_of_measurement") == "A"

    @pytest.mark.usefixtures("setup_integration")
    async def test_discharge_entity_registered(
        self,
        hass: HomeAssistant,
        slot1_discharge_current_v2_entity_id: str,
    ) -> None:
        state = hass.states.get(slot1_discharge_current_v2_entity_id)
        assert state is not None
        assert state.attributes.get("min") == InverterChargeDischargeSlot.current_min_value
        assert state.attributes.get("max") == InverterChargeDischargeSlot.current_max_value
        assert state.attributes.get("step") == InverterChargeDischargeSlot.current_step
        assert state.attributes.get("unit_of_measurement") == "A"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", "0.0"),
            ("50", "50.0"),
            ("100", "100.0"),
            ("not a number", "unknown"),
            (None, "unavailable"),
        ],
    )
    async def test_charge_current_native_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        slot1_charge_current_v2_entity_id: str,
        value: None | str,
        expected: str,
    ) -> None:
        cid = ensure(any_inverter.charge_discharge_slots).charge_slot1.current_cid
        await set_data({cid: value})

        state = get_state(hass, slot1_charge_current_v2_entity_id)
        assert state.state == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (50.4, "50"),
            (99.9, "100"),
        ],
    )
    async def test_async_set_value_charge_current(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        slot1_charge_current_v2_entity_id: str,
        value: float,
        expected_str: str,
    ) -> None:
        cid = ensure(any_inverter.charge_discharge_slots).charge_slot1.current_cid
        await set_data({cid: "10:00-12:00"})

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": slot1_charge_current_v2_entity_id, "value": value},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, expected_str)

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", "0.0"),
            ("50", "50.0"),
            ("100", "100.0"),
            ("not a number", "unknown"),
            (None, "unavailable"),
        ],
    )
    async def test_discharge_current_native_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        slot1_discharge_current_v2_entity_id: str,
        value: None | str,
        expected: str,
    ) -> None:
        cid = ensure(any_inverter.charge_discharge_slots).discharge_slot1.current_cid
        await set_data({cid: value})

        state = get_state(hass, slot1_discharge_current_v2_entity_id)
        assert state.state == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (50.4, "50"),
            (99.9, "100"),
        ],
    )
    async def test_async_set_value_discharge_current(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        slot1_discharge_current_v2_entity_id: str,
        value: float,
        expected_str: str,
    ) -> None:
        cid = ensure(any_inverter.charge_discharge_slots).discharge_slot1.current_cid
        await set_data({cid: "50"})

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": slot1_discharge_current_v2_entity_id, "value": value},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, expected_str)


class TestBatterySocV2:
    @pytest.mark.usefixtures("setup_integration")
    async def test_charge_entity_registered(
        self,
        hass: HomeAssistant,
        slot1_charge_soc_v2_entity_id: str,
    ) -> None:
        state = hass.states.get(slot1_charge_soc_v2_entity_id)
        assert state is not None
        assert state.attributes.get("min") == InverterChargeDischargeSlot.soc_min_value
        assert state.attributes.get("max") == InverterChargeDischargeSlot.soc_max_value
        assert state.attributes.get("step") == InverterChargeDischargeSlot.soc_step
        assert state.attributes.get("unit_of_measurement") == "%"

    @pytest.mark.usefixtures("setup_integration")
    async def test_discharge_entity_registered(
        self,
        hass: HomeAssistant,
        slot1_discharge_soc_v2_entity_id: str,
    ) -> None:
        state = hass.states.get(slot1_discharge_soc_v2_entity_id)
        assert state is not None
        assert state.attributes.get("min") == InverterChargeDischargeSlot.soc_min_value
        assert state.attributes.get("max") == InverterChargeDischargeSlot.soc_max_value
        assert state.attributes.get("step") == InverterChargeDischargeSlot.soc_step
        assert state.attributes.get("unit_of_measurement") == "%"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", "0.0"),
            ("50", "50.0"),
            ("100", "100.0"),
            ("not a number", "unknown"),
            (None, "unavailable"),
        ],
    )
    async def test_charge_soc_native_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        slot1_charge_soc_v2_entity_id: str,
        value: None | str,
        expected: str,
    ) -> None:
        cid = ensure(any_inverter.charge_discharge_slots).charge_slot1.soc_cid
        await set_data({cid: value})

        state = get_state(hass, slot1_charge_soc_v2_entity_id)
        assert state.state == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (50.4, "50"),
            (99.9, "100"),
        ],
    )
    async def test_async_set_value_charge_soc(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        slot1_charge_soc_v2_entity_id: str,
        value: float,
        expected_str: str,
    ) -> None:
        cid = ensure(any_inverter.charge_discharge_slots).charge_slot1.soc_cid
        await set_data({cid: "50"})

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": slot1_charge_soc_v2_entity_id, "value": value},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, expected_str)

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", "0.0"),
            ("50", "50.0"),
            ("100", "100.0"),
            ("not a number", "unknown"),
            (None, "unavailable"),
        ],
    )
    async def test_discharge_soc_native_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        slot1_discharge_soc_v2_entity_id: str,
        value: None | str,
        expected: str,
    ) -> None:
        cid = ensure(any_inverter.charge_discharge_slots).discharge_slot1.soc_cid
        await set_data({cid: value})

        state = get_state(hass, slot1_discharge_soc_v2_entity_id)
        assert state.state == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (50.4, "50"),
            (99.9, "100"),
        ],
    )
    async def test_async_set_value_discharge_soc(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        slot1_discharge_soc_v2_entity_id: str,
        value: float,
        expected_str: str,
    ) -> None:
        cid = ensure(any_inverter.charge_discharge_slots).discharge_slot1.soc_cid
        await set_data({cid: "50"})

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": slot1_discharge_soc_v2_entity_id, "value": value},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, expected_str)

    @pytest.mark.parametrize(
        ("entity_id_fixture", "slot_attr"),
        [
            ("slot1_charge_soc_v2_entity_id", "charge_slot1"),
            ("slot1_discharge_soc_v2_entity_id", "discharge_slot1"),
        ],
    )
    async def test_bounds_follow_battery_limits(
        self,
        request: pytest.FixtureRequest,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        entity_id_fixture: str,
        slot_attr: str,
    ) -> None:
        # bounds are refreshed only while the entity has its own data
        await set_data(
            {
                getattr(any_inverter.charge_discharge_slots, slot_attr).soc_cid: "50",
                ensure(any_inverter.battery_over_discharge_soc).cid: "20",
                ensure(any_inverter.battery_max_charge_soc).cid: "90",
            }
        )

        state = get_state(hass, request.getfixturevalue(entity_id_fixture))
        assert state.attributes.get("min") == 21
        assert state.attributes.get("max") == 90


class TestMaxOutputPower:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        max_output_power_entity_id: str,
    ) -> None:
        state = hass.states.get(max_output_power_entity_id)
        assert state is not None
        assert state.attributes.get("min") == InverterMaxOutputPower.min_value
        assert state.attributes.get("max") == InverterMaxOutputPower.max_value
        assert state.attributes.get("step") == InverterMaxOutputPower.step
        assert state.attributes.get("unit_of_measurement") == "%"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", "0.0"),
            ("50", "50.0"),
            ("100", "100.0"),
            ("not a number", "unknown"),
            (None, "unavailable"),
        ],
    )
    async def test_native_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        max_output_power_entity_id: str,
        value: None | str,
        expected: str,
    ) -> None:
        cid = ensure(any_inverter.max_output_power).cid
        await set_data({cid: value})

        state = get_state(hass, max_output_power_entity_id)
        assert state.state == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (50.4, "50"),
            (99.9, "100"),
        ],
    )
    async def test_async_set_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        max_output_power_entity_id: str,
        value: float,
        expected_str: str,
    ) -> None:
        cid = ensure(any_inverter.max_output_power).cid
        await set_data({cid: "50"})

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": max_output_power_entity_id, "value": value},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, expected_str)


class TestMaxExportPower:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        max_export_power_entity_id: str,
    ) -> None:
        state = hass.states.get(max_export_power_entity_id)
        assert state is not None
        assert state.attributes.get("min") == InverterMaxExportPower.min_value
        assert state.attributes.get("max") == InverterMaxExportPower.max_value
        assert state.attributes.get("step") == InverterMaxExportPower.step
        assert state.attributes.get("unit_of_measurement") == "W"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", "0.0"),
            ("50", "50.0"),
            ("100", "100.0"),
            ("not a number", "unknown"),
            (None, "unavailable"),
        ],
    )
    async def test_native_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        max_export_power_entity_id: str,
        value: None | str,
        expected: str,
    ) -> None:
        cid = ensure(any_inverter.max_export_power).cid
        await set_data({cid: value})

        state = get_state(hass, max_export_power_entity_id)
        assert state.state == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (50.4, "50"),
            (99.9, "100"),
        ],
    )
    async def test_async_set_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        max_export_power_entity_id: str,
        value: float,
        expected_str: str,
    ) -> None:
        cid = ensure(any_inverter.max_export_power).cid
        await set_data({cid: "50"})

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": max_export_power_entity_id, "value": value},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, expected_str)


class TestExportCalibration:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        export_calibration_entity_id: str,
    ) -> None:
        state = hass.states.get(export_calibration_entity_id)
        assert state is not None
        assert state.attributes.get("min") == InverterExportCalibration.min_value
        assert state.attributes.get("max") == InverterExportCalibration.max_value
        assert state.attributes.get("step") == InverterExportCalibration.step
        assert state.attributes.get("unit_of_measurement") == "W"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("-1000", "-1000.0"),
            ("0", "0.0"),
            ("50", "50.0"),
            ("1000", "1000.0"),
            ("not a number", "unknown"),
            (None, "unavailable"),
        ],
    )
    async def test_native_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        export_calibration_entity_id: str,
        value: None | str,
        expected: str,
    ) -> None:
        cid = ensure(any_inverter.export_calibration).cid
        await set_data({cid: value})

        state = get_state(hass, export_calibration_entity_id)
        assert state.state == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (50.4, "50"),
            (99.9, "100"),
        ],
    )
    async def test_async_set_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        export_calibration_entity_id: str,
        value: float,
        expected_str: str,
    ) -> None:
        cid = ensure(any_inverter.export_calibration).cid
        await set_data({cid: "50"})

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": export_calibration_entity_id, "value": value},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, expected_str)


class TestPowerLimit:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        power_limit_entity_id: str,
    ) -> None:
        state = hass.states.get(power_limit_entity_id)
        assert state is not None
        assert state.attributes.get("min") == InverterPowerLimit.min_value
        assert state.attributes.get("max") == InverterPowerLimit.max_value
        assert state.attributes.get("step") == InverterPowerLimit.step
        assert state.attributes.get("unit_of_measurement") == "%"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", "0.0"),
            ("50", "50.0"),
            ("100", "100.0"),
            ("not a number", "unknown"),
            (None, "unavailable"),
        ],
    )
    async def test_native_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        power_limit_entity_id: str,
        value: None | str,
        expected: str,
    ) -> None:
        cid = ensure(any_inverter.power_limit).cid
        await set_data({cid: value})

        state = get_state(hass, power_limit_entity_id)
        assert state.state == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (50.4, "50"),
            (99.9, "100"),
        ],
    )
    async def test_async_set_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        power_limit_entity_id: str,
        value: float,
        expected_str: str,
    ) -> None:
        cid = ensure(any_inverter.power_limit).cid
        await set_data({cid: "50"})

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": power_limit_entity_id, "value": value},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, expected_str)


class TestBatterySocNumber:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        battery_force_charge_soc_entity_id: str,
    ) -> None:
        state = hass.states.get(battery_force_charge_soc_entity_id)
        assert state is not None
        assert state.attributes.get("min") == InverterBatteryForceChargeSOC.min_value
        assert state.attributes.get("max") == InverterBatteryForceChargeSOC.max_value
        assert state.attributes.get("step") == InverterBatteryForceChargeSOC.step
        assert state.attributes.get("unit_of_measurement") == "%"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", "0.0"),
            ("50", "50.0"),
            ("100", "100.0"),
            ("not a number", "unknown"),
            (None, "unavailable"),
        ],
    )
    async def test_native_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        battery_force_charge_soc_entity_id: str,
        value: None | str,
        expected: str,
    ) -> None:
        cid = ensure(any_inverter.battery_force_charge_soc).cid
        await set_data({cid: value})

        state = get_state(hass, battery_force_charge_soc_entity_id)
        assert state.state == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (50.4, "50"),
            (99.9, "100"),
        ],
    )
    async def test_async_set_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        battery_force_charge_soc_entity_id: str,
        value: float,
        expected_str: str,
    ) -> None:
        cid = ensure(any_inverter.battery_force_charge_soc).cid
        await set_data({cid: "50"})

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": battery_force_charge_soc_entity_id, "value": value},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, expected_str)


class TestBatteryMaxCurrentNumber:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        battery_max_charge_current_entity_id: str,
    ) -> None:
        state = hass.states.get(battery_max_charge_current_entity_id)
        assert state is not None
        assert state.attributes.get("min") == InverterBatteryMaxChargeCurrent.min_value
        assert state.attributes.get("max") == InverterBatteryMaxChargeCurrent.max_value
        assert state.attributes.get("step") == InverterBatteryMaxChargeCurrent.step
        assert state.attributes.get("unit_of_measurement") == "A"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", "0.0"),
            ("10.5", "10.5"),
            ("100", "100.0"),
            ("not a number", "unknown"),
            (None, "unavailable"),
        ],
    )
    async def test_native_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        battery_max_charge_current_entity_id: str,
        value: None | str,
        expected: str,
    ) -> None:
        cid = ensure(any_inverter.battery_max_charge_current).cid
        await set_data({cid: value})

        state = get_state(hass, battery_max_charge_current_entity_id)
        assert state.state == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (10.4, "10"),
            (99.9, "100"),
        ],
    )
    async def test_async_set_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        battery_max_charge_current_entity_id: str,
        value: float,
        expected_str: str,
    ) -> None:
        cid = ensure(any_inverter.battery_max_charge_current).cid
        await set_data({cid: "50"})

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": battery_max_charge_current_entity_id, "value": value},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, expected_str)


class TestMpptScanIntervalNumber:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        mppt_scan_interval_entity_id: str,
    ) -> None:
        state = hass.states.get(mppt_scan_interval_entity_id)
        assert state is not None
        assert state.attributes.get("min") == InverterMpptScanInterval.min_value
        assert state.attributes.get("max") == InverterMpptScanInterval.max_value
        assert state.attributes.get("step") == InverterMpptScanInterval.step
        assert state.attributes.get("unit_of_measurement") == "s"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("600", "600.0"),
            ("1800", "1800.0"),
            ("10800", "10800.0"),
            ("not a number", "unknown"),
            (None, "unavailable"),
        ],
    )
    async def test_native_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        mppt_scan_interval_entity_id: str,
        value: None | str,
        expected: str,
    ) -> None:
        cid = ensure(any_inverter.mppt_scan_interval).cid
        await set_data({cid: value})

        state = get_state(hass, mppt_scan_interval_entity_id)
        assert state.state == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (600.0, "600"),
            (1800.4, "1800"),
            (10799.9, "10800"),
        ],
    )
    async def test_async_set_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        mppt_scan_interval_entity_id: str,
        value: float,
        expected_str: str,
    ) -> None:
        cid = ensure(any_inverter.mppt_scan_interval).cid
        await set_data({cid: "1800"})

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": mppt_scan_interval_entity_id, "value": value},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, expected_str)


class TestPeakShavingBaselineSoc:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        peak_shaving_baseline_soc_entity_id: str,
    ) -> None:
        state = hass.states.get(peak_shaving_baseline_soc_entity_id)
        assert state is not None
        assert state.attributes.get("min") == InverterPeakShavingBaselineSOC.min_value
        assert state.attributes.get("max") == InverterPeakShavingBaselineSOC.max_value
        assert state.attributes.get("step") == InverterPeakShavingBaselineSOC.step
        assert state.attributes.get("unit_of_measurement") == "%"

    async def test_async_set_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        peak_shaving_baseline_soc_entity_id: str,
    ) -> None:
        cid = ensure(any_inverter.peak_shaving_baseline_soc).cid
        await set_data({cid: "50"})

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": peak_shaving_baseline_soc_entity_id, "value": 40},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, "40")


class TestPeakShavingMaxUsableGridPower:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        peak_shaving_max_usable_grid_power_entity_id: str,
    ) -> None:
        state = hass.states.get(peak_shaving_max_usable_grid_power_entity_id)
        assert state is not None
        assert state.attributes.get("min") == InverterPeakShavingMaxUsableGridPower.min_value
        assert state.attributes.get("max") == InverterPeakShavingMaxUsableGridPower.max_value
        assert state.attributes.get("step") == InverterPeakShavingMaxUsableGridPower.step
        assert state.attributes.get("unit_of_measurement") == "W"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", "0.0"),
            ("5000", "5000.0"),
            ("10000", "10000.0"),
            ("not a number", "unknown"),
            (None, "unavailable"),
        ],
    )
    async def test_native_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        peak_shaving_max_usable_grid_power_entity_id: str,
        value: None | str,
        expected: str,
    ) -> None:
        cid = ensure(any_inverter.peak_shaving_max_usable_grid_power).cid
        await set_data({cid: value})

        state = get_state(hass, peak_shaving_max_usable_grid_power_entity_id)
        assert state.state == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (5000.4, "5000"),
            (9999.9, "10000"),
        ],
    )
    async def test_async_set_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        peak_shaving_max_usable_grid_power_entity_id: str,
        value: float,
        expected_str: str,
    ) -> None:
        cid = ensure(any_inverter.peak_shaving_max_usable_grid_power).cid
        await set_data({cid: "5000"})

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": peak_shaving_max_usable_grid_power_entity_id, "value": value},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, expected_str)


class TestGridPeakShavingPower:
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        grid_peak_shaving_power_entity_id: str,
    ) -> None:
        state = hass.states.get(grid_peak_shaving_power_entity_id)
        assert state is not None
        assert state.attributes.get("min") == InverterGridPeakShavingPower.min_value
        assert state.attributes.get("max") == InverterGridPeakShavingPower.max_value
        assert state.attributes.get("step") == InverterGridPeakShavingPower.step
        assert state.attributes.get("unit_of_measurement") == "W"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", "0.0"),
            ("32000", "32000.0"),
            ("64000", "64000.0"),
            ("not a number", "unknown"),
            (None, "unavailable"),
        ],
    )
    async def test_native_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        grid_peak_shaving_power_entity_id: str,
        value: None | str,
        expected: str,
    ) -> None:
        cid = ensure(any_inverter.grid_peak_shaving_power).cid
        await set_data({cid: value})

        state = get_state(hass, grid_peak_shaving_power_entity_id)
        assert state.state == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (32000.4, "32000"),
            (63999.9, "64000"),
        ],
    )
    async def test_async_set_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        grid_peak_shaving_power_entity_id: str,
        value: float,
        expected_str: str,
    ) -> None:
        cid = ensure(any_inverter.grid_peak_shaving_power).cid
        await set_data({cid: "32000"})

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": grid_peak_shaving_power_entity_id, "value": value},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, cid, expected_str)


class TestParallelBatteries:
    # max current of the slot entities scales with the number of parallel batteries
    @pytest.fixture
    def any_inverter(self, any_inverter: Inverter) -> Inverter:
        return replace(
            any_inverter,
            battery_max_charge_current=replace(
                ensure(any_inverter.battery_max_charge_current), parallel_battery_count=2
            ),
            battery_max_discharge_current=replace(
                ensure(any_inverter.battery_max_discharge_current), parallel_battery_count=2
            ),
        )

    @pytest.mark.parametrize(
        ("entity_id_fixture", "entity_cid", "max_current_attr"),
        [
            (
                "slot1_charge_current_v1_entity_id",
                lambda inverter: inverter.charge_discharge_settings.cid,
                "battery_max_charge_current",
            ),
            (
                "slot1_discharge_current_v1_entity_id",
                lambda inverter: inverter.charge_discharge_settings.cid,
                "battery_max_discharge_current",
            ),
            (
                "slot1_charge_current_v2_entity_id",
                lambda inverter: inverter.charge_discharge_slots.charge_slot1.current_cid,
                "battery_max_charge_current",
            ),
            (
                "slot1_discharge_current_v2_entity_id",
                lambda inverter: inverter.charge_discharge_slots.discharge_slot1.current_cid,
                "battery_max_discharge_current",
            ),
        ],
    )
    async def test_native_max_value(
        self,
        request: pytest.FixtureRequest,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        entity_id_fixture: str,
        entity_cid: Callable[[Inverter], int],
        max_current_attr: str,
    ) -> None:
        # bounds are refreshed only while the entity has its own data
        await set_data({entity_cid(any_inverter): "1", getattr(any_inverter, max_current_attr).cid: "50"})

        state = get_state(hass, request.getfixturevalue(entity_id_fixture))
        assert state.attributes.get("max") == 100


class TestMaxExportPowerScaled:
    @pytest.fixture
    def any_inverter(self, any_inverter: Inverter) -> Inverter:
        return replace(any_inverter, max_export_power=replace(ensure(any_inverter.max_export_power), scale=0.1))

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", "0.0"),
            ("50", "500.0"),
            ("100", "1000.0"),
            ("not a number", "unknown"),
            (None, "unavailable"),
        ],
    )
    async def test_native_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        any_inverter: Inverter,
        max_export_power_entity_id: str,
        value: None | str,
        expected: str,
    ) -> None:
        await set_data({ensure(any_inverter.max_export_power).cid: value})

        state = get_state(hass, max_export_power_entity_id)
        assert state.state == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (1, "0"),
            (504, "50"),
            (999, "100"),
        ],
    )
    async def test_async_set_value(
        self,
        hass: HomeAssistant,
        set_data: SetData,
        mock_api_client: AsyncMock,
        any_inverter: Inverter,
        max_export_power_entity_id: str,
        value: int,
        expected_str: str,
    ) -> None:
        await set_data({ensure(any_inverter.max_export_power).cid: "50"})

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": max_export_power_entity_id, "value": value},
            blocking=True,
        )

        assert_control(mock_api_client, any_inverter, ensure(any_inverter.max_export_power).cid, expected_str)
