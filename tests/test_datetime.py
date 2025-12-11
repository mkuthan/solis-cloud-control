from datetime import datetime

import pytest
from homeassistant.components.datetime import DateTimeEntityDescription

from custom_components.solis_cloud_control.datetime import InverterTimeEntity


@pytest.fixture
def inverter_time_entity(mock_coordinator, any_inverter):
    return InverterTimeEntity(
        coordinator=mock_coordinator,
        entity_description=DateTimeEntityDescription(key="any_key", name="any name"),
        inverter_time=any_inverter.time,
    )


class TestInverterTimeEntity:
    @pytest.mark.parametrize(
        ("value", "timezone", "expected"),
        [
            ("2025-12-11 17:00:00", "UTC", "2025-12-11T17:00:00+00:00"),
            ("2025-12-11 17:00:00", "Europe/Warsaw", "2025-12-11T17:00:00+01:00"),
        ],
    )
    async def test_native_value(self, hass, inverter_time_entity, value: str, timezone: str, expected: str):
        inverter_time_entity.coordinator.data = {inverter_time_entity.inverter_time.cid: value}
        await hass.config.async_set_time_zone(timezone)

        assert inverter_time_entity.native_value == datetime.fromisoformat(expected)

    def test_native_value_none(self, inverter_time_entity):
        inverter_time_entity.coordinator.data = {inverter_time_entity.inverter_time.cid: None}

        assert inverter_time_entity.native_value is None

    def test_native_value_invalid(self, inverter_time_entity):
        inverter_time_entity.coordinator.data = {inverter_time_entity.inverter_time.cid: "invalid"}

        assert inverter_time_entity.native_value is None

    @pytest.mark.parametrize(
        ("value", "timezone", "expected"),
        [
            ("2025-12-11T17:00:00+00:00", "UTC", "2025-12-11 17:00:00"),
            ("2025-12-11T17:00:00+01:00", "Europe/Warsaw", "2025-12-11 17:00:00"),
        ],
    )
    async def test_async_set_value(self, hass, inverter_time_entity, value: str, timezone: str, expected: str):
        await hass.config.async_set_time_zone(timezone)
        await inverter_time_entity.async_set_value(datetime.fromisoformat(value))

        inverter_time_entity.coordinator.control.assert_awaited_once_with(
            inverter_time_entity.inverter_time.cid, expected
        )
