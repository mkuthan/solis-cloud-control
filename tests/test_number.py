import pytest
from homeassistant.components.number import NumberEntityDescription
from homeassistant.const import PERCENTAGE, UnitOfElectricCurrent, UnitOfPower

from custom_components.solis_cloud_control.const import (
    CID_BATTERY_OVER_DISCHARGE_SOC,
    CID_CHARGE_SLOT1_CURRENT,
    CID_CHARGE_SLOT1_SOC,
    CID_MAX_EXPORT_POWER,
)
from custom_components.solis_cloud_control.number import (
    BatteryCurrent,
    BatterySoc,
    MaxExportPower,
)


@pytest.fixture
def battery_current_entity(mock_coordinator):
    return BatteryCurrent(
        coordinator=mock_coordinator,
        entity_description=NumberEntityDescription(
            key="test_current",
            name="Test Current",
        ),
        cid=CID_CHARGE_SLOT1_CURRENT,
    )


class TestBatteryCurrent:
    def test_attributes(self, battery_current_entity):
        assert battery_current_entity.native_min_value == 0
        assert battery_current_entity.native_max_value == 100
        assert battery_current_entity.native_step == 1
        assert battery_current_entity.native_unit_of_measurement == UnitOfElectricCurrent.AMPERE

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("50", 50.0),
            ("0", 0.0),
            ("100", 100.0),
            (None, None),
        ],
    )
    def test_native_value(self, battery_current_entity, value, expected):
        battery_current_entity.coordinator.data = {CID_CHARGE_SLOT1_CURRENT: value}
        assert battery_current_entity.native_value == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (50.4, "50"),
            (99.9, "100"),
        ],
    )
    async def test_set_native_value(self, battery_current_entity, value, expected_str):
        await battery_current_entity.async_set_native_value(value)
        battery_current_entity.coordinator.control.assert_awaited_once_with(CID_CHARGE_SLOT1_CURRENT, expected_str)


@pytest.fixture
def battery_soc_entity(mock_coordinator):
    return BatterySoc(
        coordinator=mock_coordinator,
        entity_description=NumberEntityDescription(
            key="test_soc",
            name="Test SOC",
        ),
        cid=CID_CHARGE_SLOT1_SOC,
    )


class TestBatterySoc:
    def test_attributes(self, battery_soc_entity):
        assert battery_soc_entity.native_min_value == 0
        assert battery_soc_entity.native_max_value == 100
        assert battery_soc_entity.native_step == 1
        assert battery_soc_entity.native_unit_of_measurement == PERCENTAGE

    @pytest.mark.parametrize(
        ("over_discharge", "expected_min"),
        [
            ("10", 11.0),
            ("0", 1.0),
            (None, 0.0),
        ],
    )
    def test_native_min_value(self, battery_soc_entity, over_discharge, expected_min):
        battery_soc_entity.coordinator.data = {CID_BATTERY_OVER_DISCHARGE_SOC: over_discharge}
        assert battery_soc_entity.native_min_value == expected_min

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("50", 50.0),
            ("0", 0.0),
            ("100", 100.0),
            (None, None),
        ],
    )
    def test_native_value(self, battery_soc_entity, value, expected):
        battery_soc_entity.coordinator.data = {CID_CHARGE_SLOT1_SOC: value}
        assert battery_soc_entity.native_value == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (0.1, "0"),
            (50.4, "50"),
            (99.9, "100"),
        ],
    )
    async def test_set_native_value(self, battery_soc_entity, value, expected_str):
        await battery_soc_entity.async_set_native_value(value)
        battery_soc_entity.coordinator.control.assert_awaited_once_with(CID_CHARGE_SLOT1_SOC, expected_str)


@pytest.fixture
def max_export_power_entity(mock_coordinator):
    return MaxExportPower(
        coordinator=mock_coordinator,
        entity_description=NumberEntityDescription(
            key="test_power",
            name="Test Power",
        ),
        cid=CID_MAX_EXPORT_POWER,
    )


class TestMaxExportPower:
    def test_attributes(self, max_export_power_entity):
        assert max_export_power_entity.native_min_value == 0
        assert max_export_power_entity.native_max_value == 13200
        assert max_export_power_entity.native_step == 100
        assert max_export_power_entity.native_unit_of_measurement == UnitOfPower.WATT

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("0", 0.0),
            ("50", 5000.0),
            ("132", 13200.0),
            (None, None),
        ],
    )
    def test_native_value(self, max_export_power_entity, value, expected):
        max_export_power_entity.coordinator.data = {CID_MAX_EXPORT_POWER: value}
        assert max_export_power_entity.native_value == expected

    @pytest.mark.parametrize(
        ("value", "expected_str"),
        [
            (100.0, "1"),
            (5000.0, "50"),
            (13200.0, "132"),
        ],
    )
    async def test_set_native_value(self, max_export_power_entity, value, expected_str):
        await max_export_power_entity.async_set_native_value(value)
        max_export_power_entity.coordinator.control.assert_awaited_once_with(CID_MAX_EXPORT_POWER, expected_str)
