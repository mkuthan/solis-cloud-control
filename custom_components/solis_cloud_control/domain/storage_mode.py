class StorageMode:
    BIT_SELF_USE: int = 0
    BIT_OFF_GRID: int = 2
    BIT_BACKUP_MODE: int = 4
    BIT_GRID_CHARGING: int = 5
    BIT_FEED_IN_PRIORITY: int = 6

    @staticmethod
    def create(value: str | None) -> "StorageMode | None":
        if value is None:
            return None

        try:
            mode = int(value)
            return StorageMode(mode)
        except ValueError:
            return None

    def __init__(self, mode: int) -> None:
        self.mode = mode

    def is_self_use(self) -> bool:
        return (self.mode & (1 << self.BIT_SELF_USE)) != 0

    def is_feed_in_priority(self) -> bool:
        return (self.mode & (1 << self.BIT_FEED_IN_PRIORITY)) != 0

    def is_off_grid(self) -> bool:
        return (self.mode & (1 << self.BIT_OFF_GRID)) != 0

    def is_battery_reserve_enabled(self) -> bool:
        return (self.mode & (1 << self.BIT_BACKUP_MODE)) != 0

    def is_allow_grid_charging(self) -> bool:
        return (self.mode & (1 << self.BIT_GRID_CHARGING)) != 0

    def set_self_use(self) -> None:
        self.mode |= 1 << self.BIT_SELF_USE
        self.mode &= ~(1 << self.BIT_FEED_IN_PRIORITY)
        self.mode &= ~(1 << self.BIT_OFF_GRID)

    def set_feed_in_priority(self) -> None:
        self.mode |= 1 << self.BIT_FEED_IN_PRIORITY
        self.mode &= ~(1 << self.BIT_SELF_USE)
        self.mode &= ~(1 << self.BIT_OFF_GRID)

    def set_off_grid(self) -> None:
        self.mode |= 1 << self.BIT_OFF_GRID
        self.mode &= ~(1 << self.BIT_SELF_USE)
        self.mode &= ~(1 << self.BIT_FEED_IN_PRIORITY)

    def enable_battery_reserve(self) -> None:
        self.mode |= 1 << self.BIT_BACKUP_MODE

    def disable_battery_reserve(self) -> None:
        self.mode &= ~(1 << self.BIT_BACKUP_MODE)

    def enable_allow_grid_charging(self) -> None:
        self.mode |= 1 << self.BIT_GRID_CHARGING

    def disable_allow_grid_charging(self) -> None:
        self.mode &= ~(1 << self.BIT_GRID_CHARGING)

    def to_value(self) -> str:
        return str(self.mode)
