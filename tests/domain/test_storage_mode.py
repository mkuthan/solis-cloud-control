import pytest

from custom_components.solis_cloud_control.domain.storage_mode import StorageMode


class TestStorageMode:
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

    def test_is_peak_shaving(self):
        storage_mode = StorageMode(2048)

        assert storage_mode.is_peak_shaving() is True

    def test_is_tou_mode(self):
        storage_mode = StorageMode(2)

        assert storage_mode.is_tou_mode() is True

    @pytest.mark.parametrize("mode", [0x0000, 0xFFFF])
    def test_set_self_use(self, mode):
        storage_mode = StorageMode(mode)
        storage_mode.set_self_use()

        assert storage_mode.is_self_use() is True
        assert storage_mode.is_feed_in_priority() is False
        assert storage_mode.is_off_grid() is False
        assert storage_mode.is_peak_shaving() is False

    @pytest.mark.parametrize("mode", [0x0000, 0xFFFF])
    def test_set_feed_in_priority(self, mode):
        storage_mode = StorageMode(mode)
        storage_mode.set_feed_in_priority()

        assert storage_mode.is_feed_in_priority() is True
        assert storage_mode.is_self_use() is False
        assert storage_mode.is_off_grid() is False
        assert storage_mode.is_peak_shaving() is False

    @pytest.mark.parametrize("mode", [0x0000, 0xFFFF])
    def test_set_off_grid(self, mode):
        storage_mode = StorageMode(mode)
        storage_mode.set_off_grid()

        assert storage_mode.is_off_grid() is True
        assert storage_mode.is_self_use() is False
        assert storage_mode.is_feed_in_priority() is False
        assert storage_mode.is_peak_shaving() is False

    @pytest.mark.parametrize("mode", [0x0000, 0xFFFF])
    def test_set_peak_shaving(self, mode):
        storage_mode = StorageMode(mode)
        storage_mode.set_peak_shaving()

        assert storage_mode.is_peak_shaving() is True
        assert storage_mode.is_self_use() is False
        assert storage_mode.is_feed_in_priority() is False
        assert storage_mode.is_off_grid() is False

    @pytest.mark.parametrize("mode", [0x0000, 0xFFFF])
    def test_set_base_mode_preserves_modifiers(self, mode):
        storage_mode = StorageMode(mode)
        storage_mode.enable_tou_mode()
        storage_mode.enable_battery_reserve()
        storage_mode.enable_allow_grid_charging()

        storage_mode.set_peak_shaving()

        assert storage_mode.is_tou_mode() is True
        assert storage_mode.is_battery_reserve_enabled() is True
        assert storage_mode.is_allow_grid_charging() is True

    def test_set_peak_shaving_clears_other_base_modes(self):
        storage_mode = StorageMode((1 << StorageMode.BIT_SELF_USE) | (1 << StorageMode.BIT_GRID_CHARGING))
        storage_mode.set_peak_shaving()

        assert storage_mode.mode == (1 << StorageMode.BIT_PEAK_SHAVING) | (1 << StorageMode.BIT_GRID_CHARGING)

    def test_set_peak_shaving_preserves_tou(self):
        # 35 == Self-Use + TOU + grid charging; TOU is a modifier, so it is kept
        storage_mode = StorageMode(35)
        storage_mode.set_peak_shaving()

        assert storage_mode.mode == 2082

    @pytest.mark.parametrize("mode", [0x0000, 0xFFFF])
    def test_enable_battery_reserve(self, mode):
        storage_mode = StorageMode(mode)
        storage_mode.enable_battery_reserve()

        assert storage_mode.is_battery_reserve_enabled() is True

    @pytest.mark.parametrize("mode", [0x0000, 0xFFFF])
    def test_disable_battery_reserve(self, mode):
        storage_mode = StorageMode(mode)
        storage_mode.disable_battery_reserve()

        assert storage_mode.is_battery_reserve_enabled() is False

    @pytest.mark.parametrize("mode", [0x0000, 0xFFFF])
    def test_enable_allow_grid_charging(self, mode):
        storage_mode = StorageMode(mode)
        storage_mode.enable_allow_grid_charging()

        assert storage_mode.is_allow_grid_charging() is True

    @pytest.mark.parametrize("mode", [0x0000, 0xFFFF])
    def test_disable_allow_grid_charging(self, mode):
        storage_mode = StorageMode(mode)
        storage_mode.disable_allow_grid_charging()

        assert storage_mode.is_allow_grid_charging() is False

    @pytest.mark.parametrize("mode", [0x0000, 0xFFFF])
    def test_enable_tou_mode(self, mode):
        storage_mode = StorageMode(mode)
        storage_mode.enable_tou_mode()

        assert storage_mode.is_tou_mode() is True

    @pytest.mark.parametrize("mode", [0x0000, 0xFFFF])
    def test_disable_tou_mode(self, mode):
        storage_mode = StorageMode(mode)
        storage_mode.disable_tou_mode()

        assert storage_mode.is_tou_mode() is False
