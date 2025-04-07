import pytest
from homeassistant.components.select import SelectEntityDescription

from custom_components.solis_cloud_control.const import CID_STORAGE_MODE
from custom_components.solis_cloud_control.select import (
    _BIT_BACKUP_MODE,
    _BIT_FEED_IN_PRIORITY,
    _BIT_GRID_CHARGING,
    _BIT_OFF_GRID,
    _BIT_SELF_USE,
    _MODE_FEED_IN_PRIORITY,
    _MODE_OFF_GRID,
    _MODE_SELF_USE,
    StorageModeSelect,
)


@pytest.fixture
def storage_mode_entity(mock_coordinator):
    mock_coordinator.data = {CID_STORAGE_MODE: "0"}

    entity = StorageModeSelect(
        coordinator=mock_coordinator,
        entity_description=SelectEntityDescription(
            key="storage_mode",
            name="Storage Mode",
            icon="mdi:solar-power",
        ),
        cid=CID_STORAGE_MODE,
    )
    return entity


class TestStorageModeSelect:
    async def test_options(self, storage_mode_entity):
        assert storage_mode_entity.options == [
            _MODE_SELF_USE,
            _MODE_FEED_IN_PRIORITY,
            _MODE_OFF_GRID,
        ]

    @pytest.mark.parametrize(
        ("value", "expected_mode"),
        [
            (str(1 << _BIT_SELF_USE), _MODE_SELF_USE),
            (str(1 << _BIT_FEED_IN_PRIORITY), _MODE_FEED_IN_PRIORITY),
            (str(1 << _BIT_OFF_GRID), _MODE_OFF_GRID),
        ],
    )
    async def test_current_option(self, storage_mode_entity, value, expected_mode):
        storage_mode_entity.coordinator.data = {CID_STORAGE_MODE: value}
        assert storage_mode_entity.current_option == expected_mode

    async def test_extra_state_attributes_on(self, storage_mode_entity):
        value = (1 << _BIT_BACKUP_MODE) | (1 << _BIT_GRID_CHARGING)
        storage_mode_entity.coordinator.data = {CID_STORAGE_MODE: str(value)}

        assert storage_mode_entity.extra_state_attributes == {
            "battery_reserve": "ON",
            "allow_grid_charging": "ON",
        }

    async def test_extra_state_attributes_off(self, storage_mode_entity):
        value = 0
        storage_mode_entity.coordinator.data = {CID_STORAGE_MODE: str(value)}

        assert storage_mode_entity.extra_state_attributes == {
            "battery_reserve": "OFF",
            "allow_grid_charging": "OFF",
        }

    @pytest.mark.parametrize(
        ("option", "expected_value"),
        [
            (_MODE_SELF_USE, str(1 << _BIT_SELF_USE)),
            (_MODE_FEED_IN_PRIORITY, str(1 << _BIT_FEED_IN_PRIORITY)),
            (_MODE_OFF_GRID, str(1 << _BIT_OFF_GRID)),
        ],
    )
    async def test_async_select_option(self, storage_mode_entity, option, expected_value):
        await storage_mode_entity.async_select_option(option)
        storage_mode_entity.coordinator.control.assert_awaited_once_with(CID_STORAGE_MODE, expected_value)
