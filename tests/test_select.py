import pytest
from homeassistant.components.select import SelectEntityDescription

from custom_components.solis_cloud_control.inverters.inverter import InverterStorageMode
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
        storage_mode = storage_mode_entity.inverter_storage_mode
        assert storage_mode_entity.options == [
            storage_mode.mode_self_use,
            storage_mode.mode_feed_in_priority,
            storage_mode.mode_off_grid,
        ]

    @pytest.mark.parametrize(
        ("value", "expected_mode"),
        [
            (str(1 << InverterStorageMode.bit_self_use), InverterStorageMode.mode_self_use),
            (str(1 << InverterStorageMode.bit_feed_in_priority), InverterStorageMode.mode_feed_in_priority),
            (str(1 << InverterStorageMode.bit_off_grid), InverterStorageMode.mode_off_grid),
            (str(0), None),
            ("not a number", None),
            (None, None),
        ],
    )
    async def test_current_option(self, storage_mode_entity, value, expected_mode):
        storage_mode_entity.coordinator.data = {storage_mode_entity.inverter_storage_mode.cid: value}
        assert storage_mode_entity.current_option == expected_mode

    @pytest.mark.parametrize(
        ("option", "expected_value"),
        [
            (InverterStorageMode.mode_self_use, str(1 << InverterStorageMode.bit_self_use)),
            (InverterStorageMode.mode_feed_in_priority, str(1 << InverterStorageMode.bit_feed_in_priority)),
            (InverterStorageMode.mode_off_grid, str(1 << InverterStorageMode.bit_off_grid)),
        ],
    )
    async def test_async_select_option(self, storage_mode_entity, option, expected_value):
        storage_mode_entity.coordinator.data = {storage_mode_entity.inverter_storage_mode.cid: 0}
        await storage_mode_entity.async_select_option(option)
        storage_mode_entity.coordinator.control.assert_awaited_once_with(
            storage_mode_entity.inverter_storage_mode.cid, expected_value
        )

    @pytest.mark.parametrize(
        "mode,bit",
        [
            (InverterStorageMode.mode_self_use, InverterStorageMode.bit_self_use),
            (InverterStorageMode.mode_feed_in_priority, InverterStorageMode.bit_feed_in_priority),
            (InverterStorageMode.mode_off_grid, InverterStorageMode.bit_off_grid),
        ],
    )
    async def test_async_select_option_preserves_other_bits(self, storage_mode_entity, mode, bit):
        other_bits = 0b10111010

        # set initial value with storage mode bits cleared
        initial_value = other_bits & ~(
            (1 << InverterStorageMode.bit_self_use)
            | (1 << InverterStorageMode.bit_feed_in_priority)
            | (1 << InverterStorageMode.bit_off_grid)
        )
        storage_mode_entity.coordinator.data = {storage_mode_entity.inverter_storage_mode.cid: initial_value}

        await storage_mode_entity.async_select_option(mode)

        expected_value = initial_value | (1 << bit)
        storage_mode_entity.coordinator.control.assert_awaited_once_with(
            storage_mode_entity.inverter_storage_mode.cid, str(expected_value)
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
        await storage_mode_entity.async_select_option(InverterStorageMode.mode_self_use)
        storage_mode_entity.coordinator.control.assert_not_awaited()
