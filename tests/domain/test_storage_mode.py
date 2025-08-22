import pytest

from custom_components.solis_cloud_control.domain.storage_mode import StorageMode


class TestStorageMode:
    STORAGE_MODE_0x0000 = StorageMode(0)
    STORAGE_MODE_0xFFFF = StorageMode(65535)

    @pytest.mark.parametrize("value", [35, "35"])
    def test_create_with_valid_value(self, value):
        storage_mode = StorageMode.create(value)

        assert storage_mode.mode == int(value)

    @pytest.mark.parametrize(
        "value",
        [None, "", "invalid value"],
    )
    def test_create_with_invalid_values(self, value: str):
        storage_mode = StorageMode.create(value)

        assert storage_mode is None

    def test_is_self_use(self):
        storage_mode = StorageMode(1)

        assert storage_mode.is_self_use() is True

    def test_is_feed_in_priority(self):
        storage_mode = StorageMode(64)

        assert storage_mode.is_feed_in_priority() is True

    def test_is_off_grid(self):
        storage_mode = StorageMode(4)

        assert storage_mode.is_off_grid() is True

    def test_is_battery_reserve_enabled(self):
        storage_mode = StorageMode(16)

        assert storage_mode.is_battery_reserve_enabled() is True

    def test_is_allow_grid_charging(self):
        storage_mode = StorageMode(32)

        assert storage_mode.is_allow_grid_charging() is True

    def test_is_tou_mode(self):
        storage_mode = StorageMode(2)

        assert storage_mode.is_tou_mode() is True

    @pytest.mark.parametrize("storage_mode", [STORAGE_MODE_0x0000, STORAGE_MODE_0xFFFF])
    def test_set_self_use(self, storage_mode):
        storage_mode.set_self_use()

        assert storage_mode.is_self_use() is True
        assert storage_mode.is_feed_in_priority() is False
        assert storage_mode.is_off_grid() is False

    @pytest.mark.parametrize("storage_mode", [STORAGE_MODE_0x0000, STORAGE_MODE_0xFFFF])
    def test_set_feed_in_priority(self, storage_mode):
        storage_mode.set_feed_in_priority()

        assert storage_mode.is_feed_in_priority() is True
        assert storage_mode.is_self_use() is False
        assert storage_mode.is_off_grid() is False

    @pytest.mark.parametrize("storage_mode", [STORAGE_MODE_0x0000, STORAGE_MODE_0xFFFF])
    def test_set_off_grid(self, storage_mode):
        storage_mode.set_off_grid()

        assert storage_mode.is_off_grid() is True
        assert storage_mode.is_self_use() is False
        assert storage_mode.is_feed_in_priority() is False

    @pytest.mark.parametrize("storage_mode", [STORAGE_MODE_0x0000, STORAGE_MODE_0xFFFF])
    def test_enable_battery_reserve(self, storage_mode):
        storage_mode.enable_battery_reserve()

        assert storage_mode.is_battery_reserve_enabled() is True

    @pytest.mark.parametrize("storage_mode", [STORAGE_MODE_0x0000, STORAGE_MODE_0xFFFF])
    def test_disable_battery_reserve(self, storage_mode):
        storage_mode.disable_battery_reserve()

        assert storage_mode.is_battery_reserve_enabled() is False

    @pytest.mark.parametrize("storage_mode", [STORAGE_MODE_0x0000, STORAGE_MODE_0xFFFF])
    def test_enable_allow_grid_charging(self, storage_mode):
        storage_mode.enable_allow_grid_charging()

        assert storage_mode.is_allow_grid_charging() is True

    @pytest.mark.parametrize("storage_mode", [STORAGE_MODE_0x0000, STORAGE_MODE_0xFFFF])
    def test_disable_allow_grid_charging(self, storage_mode):
        storage_mode.disable_allow_grid_charging()

        assert storage_mode.is_allow_grid_charging() is False

    @pytest.mark.parametrize("storage_mode", [STORAGE_MODE_0x0000, STORAGE_MODE_0xFFFF])
    def test_enable_tou_mode(self, storage_mode):
        storage_mode.enable_tou_mode()

        assert storage_mode.is_tou_mode() is True

    @pytest.mark.parametrize("storage_mode", [STORAGE_MODE_0x0000, STORAGE_MODE_0xFFFF])
    def test_disable_tou_mode(self, storage_mode):
        storage_mode.disable_tou_mode()

        assert storage_mode.is_tou_mode() is False
