import pytest
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from custom_components.solis_cloud_control.inverters.inverter import (
    Inverter,
    InverterBatteryForceChargeSOC,
    InverterBatteryMaxChargeCurrent,
    InverterChargeDischargeSettings,
    InverterChargeDischargeSlot,
    InverterExportCalibration,
    InverterMaxExportPower,
    InverterMaxOutputPower,
    InverterMpptScanInterval,
    InverterPowerLimit,
)


@pytest.fixture
def slot1_charge_current_v1_entity_id(any_inverter: Inverter) -> str:
    # V1 entities created FIRST, get base entity_id (no suffix)
    return f"number.inverter_control_{any_inverter.info.serial_number}_slot1_charge_current"


@pytest.fixture
def slot1_discharge_current_v1_entity_id(any_inverter: Inverter) -> str:
    return f"number.inverter_control_{any_inverter.info.serial_number}_slot1_discharge_current"


@pytest.fixture
def slot1_charge_current_v2_entity_id(any_inverter: Inverter) -> str:
    # V2 entities created SECOND, get _2 suffix
    return f"number.inverter_control_{any_inverter.info.serial_number}_slot1_charge_current_2"


@pytest.fixture
def slot1_discharge_current_v2_entity_id(any_inverter: Inverter) -> str:
    # V2 entities created SECOND, get _2 suffix
    return f"number.inverter_control_{any_inverter.info.serial_number}_slot1_discharge_current_2"


@pytest.fixture
def slot1_charge_soc_v2_entity_id(any_inverter: Inverter) -> str:
    return f"number.inverter_control_{any_inverter.info.serial_number}_slot1_charge_soc"


@pytest.fixture
def slot1_discharge_soc_v2_entity_id(any_inverter: Inverter) -> str:
    return f"number.inverter_control_{any_inverter.info.serial_number}_slot1_discharge_soc"


@pytest.fixture
def max_output_power_entity_id(any_inverter: Inverter) -> str:
    return f"number.inverter_control_{any_inverter.info.serial_number}_max_output_power"


@pytest.fixture
def max_export_power_entity_id(any_inverter: Inverter) -> str:
    return f"number.inverter_control_{any_inverter.info.serial_number}_max_export_power"


@pytest.fixture
def export_calibration_entity_id(any_inverter: Inverter) -> str:
    return f"number.inverter_control_{any_inverter.info.serial_number}_export_calibration"


@pytest.fixture
def power_limit_entity_id(any_inverter: Inverter) -> str:
    return f"number.inverter_control_{any_inverter.info.serial_number}_power_limit"


@pytest.fixture
def battery_force_charge_soc_entity_id(any_inverter: Inverter) -> str:
    return f"number.inverter_control_{any_inverter.info.serial_number}_battery_force_charge_soc"


@pytest.fixture
def battery_max_charge_current_entity_id(any_inverter: Inverter) -> str:
    return f"number.inverter_control_{any_inverter.info.serial_number}_battery_max_charge_current"


@pytest.fixture
def mppt_scan_interval_entity_id(any_inverter: Inverter) -> str:
    # Entity ID is based on name "MPPT Multi-peak Scan Interval" -> mppt_multi_peak_scan_interval
    return f"number.inverter_control_{any_inverter.info.serial_number}_mppt_multi_peak_scan_interval"


class TestBatteryCurrentV1:
    VARIANT1_VALUE = "50,0,09:00,10:00,11:00,12:00,0,0,12:30,13:30,14:30,15:30,0,100,16:00,17:00,18:00,19:00"
    VARIANT2_VALUE = "50,0,09:00-10:00,11:00-12:00,0,0,12:30-13:30,14:30-15:30,0,100,16:00-17:00,18:00-19:00"

    async def test_charge_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        slot1_charge_current_v1_entity_id: str,
    ) -> None:
        state = hass.states.get(slot1_charge_current_v1_entity_id)
        assert state is not None
        assert state.attributes.get("min") == InverterChargeDischargeSettings.current_min_value
        assert state.attributes.get("max") == InverterChargeDischargeSettings.current_max_value
        assert state.attributes.get("step") == InverterChargeDischargeSettings.current_step
        assert state.attributes.get("unit_of_measurement") == "A"

    async def test_discharge_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
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
        setup_integration,
        any_inverter: Inverter,
        slot1_charge_current_v1_entity_id: str,
        value,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.charge_discharge_settings.cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(slot1_charge_current_v1_entity_id)
        assert state.state == "50.0"

    @pytest.mark.parametrize("value", [VARIANT1_VALUE, VARIANT2_VALUE])
    async def test_discharge_current_native_value(
        self,
        hass: HomeAssistant,
        setup_integration,
        any_inverter: Inverter,
        slot1_discharge_current_v1_entity_id: str,
        value,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.charge_discharge_settings.cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(slot1_discharge_current_v1_entity_id)
        assert state.state == "0.0"

    async def test_charge_current_native_value_no_data(
        self,
        hass: HomeAssistant,
        setup_integration,
        any_inverter: Inverter,
        slot1_charge_current_v1_entity_id: str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.charge_discharge_settings.cid
        new_data = dict(coordinator.data)
        new_data[cid] = None

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(slot1_charge_current_v1_entity_id)
        assert state.state in ("unavailable", "unknown")

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
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        slot1_charge_current_v1_entity_id: str,
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
            Platform.NUMBER,
            "set_value",
            {"entity_id": slot1_charge_current_v1_entity_id, "value": 99},
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
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        slot1_discharge_current_v1_entity_id: str,
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
            Platform.NUMBER,
            "set_value",
            {"entity_id": slot1_discharge_current_v1_entity_id, "value": 99},
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
        slot1_charge_current_v1_entity_id: str,
        initial_value,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.charge_discharge_settings.cid
        new_data = dict(coordinator.data)
        new_data[cid] = initial_value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": slot1_charge_current_v1_entity_id, "value": 99},
            blocking=True,
        )

        mock_api_client.control.assert_not_awaited()


class TestBatteryCurrentV2:
    async def test_charge_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        slot1_charge_current_v2_entity_id: str,
    ) -> None:
        state = hass.states.get(slot1_charge_current_v2_entity_id)
        assert state is not None
        assert state.attributes.get("min") == InverterChargeDischargeSlot.current_min_value
        assert state.attributes.get("max") == InverterChargeDischargeSlot.current_max_value
        assert state.attributes.get("step") == InverterChargeDischargeSlot.current_step
        assert state.attributes.get("unit_of_measurement") == "A"

    async def test_discharge_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
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
        setup_integration,
        any_inverter: Inverter,
        slot1_charge_current_v2_entity_id: str,
        value,
        expected,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.charge_discharge_slots.charge_slot1.current_cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(slot1_charge_current_v2_entity_id)
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
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        slot1_charge_current_v2_entity_id: str,
        value,
        expected_str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.charge_discharge_slots.charge_slot1.current_cid
        new_data = dict(coordinator.data)
        new_data[cid] = "10:00-12:00"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": slot1_charge_current_v2_entity_id, "value": value},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            expected_str,
            None,
        )


class TestBatterySocV2:
    async def test_charge_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        slot1_charge_soc_v2_entity_id: str,
    ) -> None:
        state = hass.states.get(slot1_charge_soc_v2_entity_id)
        assert state is not None
        assert state.attributes.get("min") == InverterChargeDischargeSlot.soc_min_value
        assert state.attributes.get("max") == InverterChargeDischargeSlot.soc_max_value
        assert state.attributes.get("step") == InverterChargeDischargeSlot.soc_step
        assert state.attributes.get("unit_of_measurement") == "%"

    async def test_discharge_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
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
        setup_integration,
        any_inverter: Inverter,
        slot1_charge_soc_v2_entity_id: str,
        value,
        expected,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.charge_discharge_slots.charge_slot1.soc_cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(slot1_charge_soc_v2_entity_id)
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
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        slot1_charge_soc_v2_entity_id: str,
        value,
        expected_str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.charge_discharge_slots.charge_slot1.soc_cid
        new_data = dict(coordinator.data)
        new_data[cid] = "50"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": slot1_charge_soc_v2_entity_id, "value": value},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            expected_str,
            None,
        )


class TestMaxOutputPower:
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
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
        setup_integration,
        any_inverter: Inverter,
        max_output_power_entity_id: str,
        value,
        expected,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.max_output_power.cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(max_output_power_entity_id)
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
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        max_output_power_entity_id: str,
        value,
        expected_str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.max_output_power.cid
        new_data = dict(coordinator.data)
        new_data[cid] = "50"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": max_output_power_entity_id, "value": value},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            expected_str,
            None,
        )


class TestMaxExportPower:
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
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
        setup_integration,
        any_inverter: Inverter,
        max_export_power_entity_id: str,
        value,
        expected,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.max_export_power.cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(max_export_power_entity_id)
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
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        max_export_power_entity_id: str,
        value,
        expected_str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.max_export_power.cid
        new_data = dict(coordinator.data)
        new_data[cid] = "50"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": max_export_power_entity_id, "value": value},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            expected_str,
            None,
        )


class TestExportCalibration:
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
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
        setup_integration,
        any_inverter: Inverter,
        export_calibration_entity_id: str,
        value,
        expected,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.export_calibration.cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(export_calibration_entity_id)
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
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        export_calibration_entity_id: str,
        value,
        expected_str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.export_calibration.cid
        new_data = dict(coordinator.data)
        new_data[cid] = "50"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": export_calibration_entity_id, "value": value},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            expected_str,
            None,
        )


class TestPowerLimit:
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
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
        setup_integration,
        any_inverter: Inverter,
        power_limit_entity_id: str,
        value,
        expected,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.power_limit.cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(power_limit_entity_id)
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
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        power_limit_entity_id: str,
        value,
        expected_str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.power_limit.cid
        new_data = dict(coordinator.data)
        new_data[cid] = "50"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": power_limit_entity_id, "value": value},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            expected_str,
            None,
        )


class TestBatterySocNumber:
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
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
        setup_integration,
        any_inverter: Inverter,
        battery_force_charge_soc_entity_id: str,
        value,
        expected,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.battery_force_charge_soc.cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(battery_force_charge_soc_entity_id)
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
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        battery_force_charge_soc_entity_id: str,
        value,
        expected_str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.battery_force_charge_soc.cid
        new_data = dict(coordinator.data)
        new_data[cid] = "50"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": battery_force_charge_soc_entity_id, "value": value},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            expected_str,
            None,
        )


class TestBatteryMaxCurrentNumber:
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
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
        setup_integration,
        any_inverter: Inverter,
        battery_max_charge_current_entity_id: str,
        value,
        expected,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.battery_max_charge_current.cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(battery_max_charge_current_entity_id)
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
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        battery_max_charge_current_entity_id: str,
        value,
        expected_str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.battery_max_charge_current.cid
        new_data = dict(coordinator.data)
        new_data[cid] = "50"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": battery_max_charge_current_entity_id, "value": value},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            expected_str,
            None,
        )


class TestMpptScanIntervalNumber:
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
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
        setup_integration,
        any_inverter: Inverter,
        mppt_scan_interval_entity_id: str,
        value,
        expected,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.mppt_scan_interval.cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        state = hass.states.get(mppt_scan_interval_entity_id)
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
        setup_integration,
        mock_api_client,
        any_inverter: Inverter,
        mppt_scan_interval_entity_id: str,
        value,
        expected_str,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = any_inverter.mppt_scan_interval.cid
        new_data = dict(coordinator.data)
        new_data[cid] = "1800"

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        await hass.services.async_call(
            Platform.NUMBER,
            "set_value",
            {"entity_id": mppt_scan_interval_entity_id, "value": value},
            blocking=True,
        )

        mock_api_client.control.assert_awaited_once_with(
            any_inverter.info.serial_number,
            cid,
            expected_str,
            None,
        )
