import pytest
from homeassistant.const import PERCENTAGE, Platform, UnitOfElectricCurrent
from homeassistant.core import HomeAssistant

from custom_components.solis_cloud_control.inverters.inverter import Inverter


@pytest.fixture
def battery_reserve_soc_entity_id(get_entity_id) -> str:
    return get_entity_id(Platform.SENSOR, "battery_reserve_soc")


@pytest.fixture
def battery_over_discharge_soc_entity_id(get_entity_id) -> str:
    return get_entity_id(Platform.SENSOR, "battery_over_discharge_soc")


@pytest.fixture
def battery_force_charge_soc_entity_id(get_entity_id) -> str:
    return get_entity_id(Platform.SENSOR, "battery_force_charge_soc")


@pytest.fixture
def battery_recovery_soc_entity_id(get_entity_id) -> str:
    return get_entity_id(Platform.SENSOR, "battery_recovery_soc")


@pytest.fixture
def battery_max_charge_soc_entity_id(get_entity_id) -> str:
    return get_entity_id(Platform.SENSOR, "battery_max_charge_soc")


@pytest.fixture
def battery_max_charge_current_entity_id(get_entity_id) -> str:
    return get_entity_id(Platform.SENSOR, "battery_max_charge_current")


@pytest.fixture
def battery_max_discharge_current_entity_id(get_entity_id) -> str:
    return get_entity_id(Platform.SENSOR, "battery_max_discharge_current")


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
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
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
        set_data,
        any_inverter: Inverter,
        entity_id_fixture: str,
        cid_attr: str,
        value,
        expected,
        request: pytest.FixtureRequest,
    ):
        cid = getattr(any_inverter, cid_attr).cid
        await set_data({cid: value})

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
        ("value", "expected_state"),
        [
            ("not a number", "unknown"),
            (None, "unavailable"),
        ],
    )
    async def test_native_value_invalid(
        self,
        hass: HomeAssistant,
        set_data,
        any_inverter: Inverter,
        entity_id_fixture: str,
        cid_attr: str,
        value,
        expected_state,
        request: pytest.FixtureRequest,
    ):
        cid = getattr(any_inverter, cid_attr).cid
        await set_data({cid: value})

        entity_id = request.getfixturevalue(entity_id_fixture)
        state = hass.states.get(entity_id)
        assert state.state == expected_state


class TestBatteryCurrentSensorsIntegration:
    @pytest.mark.parametrize(
        "entity_id_fixture",
        [
            "battery_max_charge_current_entity_id",
            "battery_max_discharge_current_entity_id",
        ],
    )
    @pytest.mark.usefixtures("setup_integration")
    async def test_entity_registered(
        self,
        hass: HomeAssistant,
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
        set_data,
        any_inverter: Inverter,
        entity_id_fixture: str,
        cid_attr: str,
        value,
        expected,
        request: pytest.FixtureRequest,
    ):
        cid = getattr(any_inverter, cid_attr).cid
        await set_data({cid: value})

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
        ("value", "expected_state"),
        [
            ("not a number", "unknown"),
            (None, "unavailable"),
        ],
    )
    async def test_native_value_invalid(
        self,
        hass: HomeAssistant,
        set_data,
        any_inverter: Inverter,
        entity_id_fixture: str,
        cid_attr: str,
        value,
        expected_state,
        request: pytest.FixtureRequest,
    ):
        cid = getattr(any_inverter, cid_attr).cid
        await set_data({cid: value})

        entity_id = request.getfixturevalue(entity_id_fixture)
        state = hass.states.get(entity_id)
        assert state.state == expected_state
