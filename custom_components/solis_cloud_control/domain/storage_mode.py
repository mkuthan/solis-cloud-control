from custom_components.solis_cloud_control.utils.safe_converters import safe_get_int_value


class StorageMode:
    BIT_SELF_USE: int = 0
    BIT_TOU_MODE: int = 1
    BIT_OFF_GRID: int = 2
    BIT_BACKUP_MODE: int = 4
    BIT_GRID_CHARGING: int = 5
    BIT_FEED_IN_PRIORITY: int = 6
    BIT_PEAK_SHAVING: int = 11

    @staticmethod
    def create(value: str | None) -> "StorageMode | None":
        mode = safe_get_int_value(value)
        return StorageMode(mode) if mode is not None else None

    def __init__(self, mode: int) -> None:
        self.mode = mode

    def is_self_use(self) -> bool:
        return (self.mode & (1 << self.BIT_SELF_USE)) != 0

    def is_feed_in_priority(self) -> bool:
        return (self.mode & (1 << self.BIT_FEED_IN_PRIORITY)) != 0

    def is_off_grid(self) -> bool:
        return (self.mode & (1 << self.BIT_OFF_GRID)) != 0

    def is_peak_shaving(self) -> bool:
        return (self.mode & (1 << self.BIT_PEAK_SHAVING)) != 0

    def is_battery_reserve_enabled(self) -> bool:
        return (self.mode & (1 << self.BIT_BACKUP_MODE)) != 0

    def is_allow_grid_charging(self) -> bool:
        return (self.mode & (1 << self.BIT_GRID_CHARGING)) != 0

    def is_tou_mode(self) -> bool:
        return (self.mode & (1 << self.BIT_TOU_MODE)) != 0

    def set_self_use(self) -> None:
        self.mode |= 1 << self.BIT_SELF_USE
        self.mode &= ~(1 << self.BIT_FEED_IN_PRIORITY)
        self.mode &= ~(1 << self.BIT_OFF_GRID)
        self.mode &= ~(1 << self.BIT_PEAK_SHAVING)

    def set_feed_in_priority(self) -> None:
        self.mode |= 1 << self.BIT_FEED_IN_PRIORITY
        self.mode &= ~(1 << self.BIT_SELF_USE)
        self.mode &= ~(1 << self.BIT_OFF_GRID)
        self.mode &= ~(1 << self.BIT_PEAK_SHAVING)

    def set_off_grid(self) -> None:
        self.mode |= 1 << self.BIT_OFF_GRID
        self.mode &= ~(1 << self.BIT_SELF_USE)
        self.mode &= ~(1 << self.BIT_FEED_IN_PRIORITY)
        self.mode &= ~(1 << self.BIT_PEAK_SHAVING)

    def set_peak_shaving(self) -> None:
        self.mode |= 1 << self.BIT_PEAK_SHAVING
        self.mode &= ~(1 << self.BIT_SELF_USE)
        self.mode &= ~(1 << self.BIT_FEED_IN_PRIORITY)
        self.mode &= ~(1 << self.BIT_OFF_GRID)

    def enable_battery_reserve(self) -> None:
        self.mode |= 1 << self.BIT_BACKUP_MODE

    def disable_battery_reserve(self) -> None:
        self.mode &= ~(1 << self.BIT_BACKUP_MODE)

    def enable_allow_grid_charging(self) -> None:
        self.mode |= 1 << self.BIT_GRID_CHARGING

    def disable_allow_grid_charging(self) -> None:
        self.mode &= ~(1 << self.BIT_GRID_CHARGING)

    def enable_tou_mode(self) -> None:
        self.mode |= 1 << self.BIT_TOU_MODE

    def disable_tou_mode(self) -> None:
        self.mode &= ~(1 << self.BIT_TOU_MODE)

    def to_value(self) -> str:
        return str(self.mode)
