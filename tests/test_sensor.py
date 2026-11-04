import pytest
from homeassistant.const import PERCENTAGE, UnitOfElectricCurrent
from homeassistant.core import HomeAssistant

from custom_components.solis_cloud_control.inverters.inverter import Inverter


@pytest.fixture
def battery_reserve_soc_entity_id(any_inverter: Inverter) -> str:
    return f"sensor.inverter_control_{any_inverter.info.serial_number}_battery_reserve_soc_deprecated"


@pytest.fixture
def battery_over_discharge_soc_entity_id(any_inverter: Inverter) -> str:
    return f"sensor.inverter_control_{any_inverter.info.serial_number}_battery_over_discharge_soc_deprecated"


@pytest.fixture
def battery_force_charge_soc_entity_id(any_inverter: Inverter) -> str:
    return f"sensor.inverter_control_{any_inverter.info.serial_number}_battery_force_charge_soc_deprecated"


@pytest.fixture
def battery_recovery_soc_entity_id(any_inverter: Inverter) -> str:
    return f"sensor.inverter_control_{any_inverter.info.serial_number}_battery_recovery_soc_deprecated"


@pytest.fixture
def battery_max_charge_soc_entity_id(any_inverter: Inverter) -> str:
    return f"sensor.inverter_control_{any_inverter.info.serial_number}_battery_max_charge_soc_deprecated"


@pytest.fixture
def battery_max_charge_current_entity_id(any_inverter: Inverter) -> str:
    return f"sensor.inverter_control_{any_inverter.info.serial_number}_battery_max_charge_current_deprecated"


@pytest.fixture
def battery_max_discharge_current_entity_id(any_inverter: Inverter) -> str:
    return f"sensor.inverter_control_{any_inverter.info.serial_number}_battery_max_discharge_current_deprecated"


class TestBatterySocSensorsIntegration:
    @pytest.mark.parametrize(
        "entity_id_fixture",
        [
            "battery_reserve_soc_entity_id",
            "battery_over_discharge_soc_entity_id",
            "battery_force_charge_soc_entity_id",
            "battery_recovery_soc_entity_id",
            "battery_max_charge_soc_entity_id",
        ],
    )
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        any_inverter: Inverter,  # noqa: ARG002
        entity_id_fixture: str,
        request: pytest.FixtureRequest,
    ):
        entity_id = request.getfixturevalue(entity_id_fixture)
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.attributes.get("unit_of_measurement") == PERCENTAGE

    @pytest.mark.parametrize(
        ("entity_id_fixture", "cid_attr"),
        [
            ("battery_reserve_soc_entity_id", "battery_reserve_soc"),
            ("battery_over_discharge_soc_entity_id", "battery_over_discharge_soc"),
            ("battery_force_charge_soc_entity_id", "battery_force_charge_soc"),
            ("battery_recovery_soc_entity_id", "battery_recovery_soc"),
            ("battery_max_charge_soc_entity_id", "battery_max_charge_soc"),
        ],
    )
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", 0.0),
            ("50", 50.0),
            ("100", 100.0),
        ],
    )
    async def test_native_value_valid(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        any_inverter: Inverter,  # noqa: ARG002
        entity_id_fixture: str,
        cid_attr: str,
        value,
        expected,
        request: pytest.FixtureRequest,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = getattr(any_inverter, cid_attr).cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        entity_id = request.getfixturevalue(entity_id_fixture)
        state = hass.states.get(entity_id)
        assert float(state.state) == expected

    @pytest.mark.parametrize(
        ("entity_id_fixture", "cid_attr"),
        [
            ("battery_reserve_soc_entity_id", "battery_reserve_soc"),
            ("battery_over_discharge_soc_entity_id", "battery_over_discharge_soc"),
            ("battery_force_charge_soc_entity_id", "battery_force_charge_soc"),
            ("battery_recovery_soc_entity_id", "battery_recovery_soc"),
            ("battery_max_charge_soc_entity_id", "battery_max_charge_soc"),
        ],
    )
    @pytest.mark.parametrize(
        "value",
        [
            "not a number",
            None,
        ],
    )
    async def test_native_value_invalid(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        any_inverter: Inverter,  # noqa: ARG002
        entity_id_fixture: str,
        cid_attr: str,
        value,
        request: pytest.FixtureRequest,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = getattr(any_inverter, cid_attr).cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        entity_id = request.getfixturevalue(entity_id_fixture)
        state = hass.states.get(entity_id)
        assert state.state in ("unavailable", "unknown")


class TestBatteryCurrentSensorsIntegration:
    @pytest.mark.parametrize(
        "entity_id_fixture",
        [
            "battery_max_charge_current_entity_id",
            "battery_max_discharge_current_entity_id",
        ],
    )
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        any_inverter: Inverter,  # noqa: ARG002
        entity_id_fixture: str,
        request: pytest.FixtureRequest,
    ):
        entity_id = request.getfixturevalue(entity_id_fixture)
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.attributes.get("unit_of_measurement") == UnitOfElectricCurrent.AMPERE

    @pytest.mark.parametrize(
        ("entity_id_fixture", "cid_attr"),
        [
            ("battery_max_charge_current_entity_id", "battery_max_charge_current"),
            ("battery_max_discharge_current_entity_id", "battery_max_discharge_current"),
        ],
    )
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", 0.0),
            ("10.5", 10.5),
            ("100", 100.0),
        ],
    )
    async def test_native_value_valid(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        any_inverter: Inverter,  # noqa: ARG002
        entity_id_fixture: str,
        cid_attr: str,
        value,
        expected,
        request: pytest.FixtureRequest,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = getattr(any_inverter, cid_attr).cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        entity_id = request.getfixturevalue(entity_id_fixture)
        state = hass.states.get(entity_id)
        assert float(state.state) == expected

    @pytest.mark.parametrize(
        ("entity_id_fixture", "cid_attr"),
        [
            ("battery_max_charge_current_entity_id", "battery_max_charge_current"),
            ("battery_max_discharge_current_entity_id", "battery_max_discharge_current"),
        ],
    )
    @pytest.mark.parametrize(
        "value",
        [
            "not a number",
            None,
        ],
    )
    async def test_native_value_invalid(
        self,
        hass: HomeAssistant,
        setup_integration,  # noqa: ARG002
        any_inverter: Inverter,  # noqa: ARG002
        entity_id_fixture: str,
        cid_attr: str,
        value,
        request: pytest.FixtureRequest,
    ):
        coordinator = setup_integration.runtime_data.coordinator
        cid = getattr(any_inverter, cid_attr).cid
        new_data = dict(coordinator.data)
        new_data[cid] = value

        coordinator.async_set_updated_data(new_data)
        await hass.async_block_till_done()

        entity_id = request.getfixturevalue(entity_id_fixture)
        state = hass.states.get(entity_id)
        assert state.state in ("unavailable", "unknown")
