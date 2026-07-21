import pytest
from homeassistant.components.select import SelectEntityDescription

from custom_components.solis_cloud_control.domain.storage_mode import StorageMode
from custom_components.solis_cloud_control.select import StorageModeSelect


@pytest.fixture
def storage_mode_entity(mock_coordinator, any_inverter):
    return StorageModeSelect(
        coordinator=mock_coordinator,
        entity_description=SelectEntityDescription(key="any_key", name="any name"),
        inverter_storage_mode=any_inverter.storage_mode,
    )


class TestStorageModeSelect:
    async def test_options(self, storage_mode_entity):
        assert storage_mode_entity.options == [
            storage_mode_entity.MODE_SELF_USE,
            storage_mode_entity.MODE_FEED_IN_PRIORITY,
            storage_mode_entity.MODE_OFF_GRID,
            storage_mode_entity.MODE_GRID_PEAK_SHAVING,
        ]

    @pytest.mark.parametrize(
        ("value", "expected_mode"),
        [
            (str(1 << StorageMode.BIT_SELF_USE), StorageModeSelect.MODE_SELF_USE),
            (str(1 << StorageMode.BIT_FEED_IN_PRIORITY), StorageModeSelect.MODE_FEED_IN_PRIORITY),
            (str(1 << StorageMode.BIT_OFF_GRID), StorageModeSelect.MODE_OFF_GRID),
            (str(1 << StorageMode.BIT_PEAK_SHAVING), StorageModeSelect.MODE_GRID_PEAK_SHAVING),
            (str(0), None),
            ("not a number", None),
            (None, None),
        ],
    )
    async def test_current_option(self, storage_mode_entity, value, expected_mode):
        storage_mode_entity.coordinator.data = {storage_mode_entity.inverter_storage_mode.cid: value}
        assert storage_mode_entity.current_option == expected_mode

    @pytest.mark.parametrize(
        ("mode", "expected_value"),
        [
            (StorageModeSelect.MODE_SELF_USE, str(1 << StorageMode.BIT_SELF_USE)),
            (StorageModeSelect.MODE_FEED_IN_PRIORITY, str(1 << StorageMode.BIT_FEED_IN_PRIORITY)),
            (StorageModeSelect.MODE_OFF_GRID, str(1 << StorageMode.BIT_OFF_GRID)),
            (StorageModeSelect.MODE_GRID_PEAK_SHAVING, str(1 << StorageMode.BIT_PEAK_SHAVING)),
        ],
    )
    async def test_async_select_option(self, storage_mode_entity, mode, expected_value):
        storage_mode_entity.coordinator.data = {storage_mode_entity.inverter_storage_mode.cid: 0}
        await storage_mode_entity.async_select_option(mode)
        storage_mode_entity.coordinator.control.assert_awaited_once_with(
            storage_mode_entity.inverter_storage_mode.cid, expected_value
        )

    @pytest.mark.parametrize(
        "initial_value",
        [
            "not a number",
            None,
        ],
    )
    async def test_async_select_option_invalid_initial(self, storage_mode_entity, initial_value):
        storage_mode_entity.coordinator.data = {storage_mode_entity.inverter_storage_mode.cid: initial_value}
        await storage_mode_entity.async_select_option(StorageModeSelect.MODE_SELF_USE)
        storage_mode_entity.coordinator.control.assert_not_awaited()
