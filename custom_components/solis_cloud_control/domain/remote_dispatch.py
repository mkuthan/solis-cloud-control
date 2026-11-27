"""Remote Dispatch domain values and private Solis register mapping."""

from dataclasses import dataclass, replace
from datetime import time as _time
from enum import StrEnum
from typing import TYPE_CHECKING

from custom_components.solis_cloud_control.utils import modbus as _modbus

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class DispatchMode(StrEnum):
    BATTERY_HOLD = "battery_hold"
    BATTERY_POWER = "battery_power"
    GRID_POWER = "grid_power"
    GRID_PORT_POWER = "grid_port_power"
    SELF_CONSUMPTION = "self_consumption"
    FEED_IN_PRIORITY = "feed_in_priority"


class DispatchRunningState(StrEnum):
    STOPPED = "stopped"
    STANDBY = "standby"
    REALTIME = "realtime"
    SCHEDULED = "scheduled"


class DispatchFunction(StrEnum):
    PV_SHUTDOWN = "pv_shutdown"
    DIGITAL_OUTPUT_CLOSED = "digital_output_closed"
    ALLOW_GRID_CHARGE = "allow_grid_charge"
    OFF_GRID_BATTERY_STANDBY = "off_grid_battery_standby"
    BATTERY_RESERVE_ENABLED = "battery_reserve_enabled"
    DISABLE_DISCHARGE = "disable_discharge"
    DEMAND_CONTROL_ENABLED = "demand_control_enabled"
    PV_LIMIT_ENABLED = "pv_limit_enabled"


@dataclass(frozen=True)
class DispatchCapabilities:
    supported: bool
    version: int | None

    @property
    def known_version(self) -> bool:
        return self.supported and self.version in (1, 2, 3)

    @property
    def supports_battery_reserve(self) -> bool:
        return self.supported and self.version in (2, 3)

    @property
    def supports_discharge_prohibition(self) -> bool:
        return self.supports_battery_reserve

    @property
    def supports_demand_control(self) -> bool:
        return self.supports_battery_reserve

    @property
    def supports_pv_limit(self) -> bool:
        return self.supported and self.version == 3

    @property
    def supported_modes(self) -> tuple[DispatchMode, ...]:
        if not self.known_version:
            return ()
        base = (
            DispatchMode.BATTERY_HOLD,
            DispatchMode.BATTERY_POWER,
            DispatchMode.GRID_POWER,
            DispatchMode.GRID_PORT_POWER,
        )
        if self.version in (2, 3):
            return (*base, DispatchMode.SELF_CONSUMPTION, DispatchMode.FEED_IN_PRIORITY)
        return base


@dataclass(frozen=True)
class DispatchStatus:
    state: DispatchRunningState | None
    active_mode: DispatchMode | None


@dataclass(frozen=True)
class DispatchPowerLimit:
    enabled: bool
    watts: int | None  # None means the inverter's default


@dataclass(frozen=True)
class DispatchSettings:
    enabled: bool | None
    failsafe_minutes: int
    import_limit: DispatchPowerLimit
    export_limit: DispatchPowerLimit

    @property
    def import_limit_enabled(self) -> bool:
        return self.import_limit.enabled

    @property
    def import_limit_watts(self) -> int | None:
        return self.import_limit.watts

    @property
    def export_limit_enabled(self) -> bool:
        return self.export_limit.enabled

    @property
    def export_limit_watts(self) -> int | None:
        return self.export_limit.watts


@dataclass(frozen=True)
class DispatchFunctions:
    """None means no valid directive is reported, or the feature is unsupported."""

    pv_shutdown: bool | None = None
    digital_output_closed: bool | None = None
    allow_grid_charge: bool | None = None
    off_grid_battery_standby: bool | None = None
    battery_reserve_enabled: bool | None = None
    disable_discharge: bool | None = None
    demand_control_enabled: bool | None = None
    pv_limit_enabled: bool | None = None

    def value_of(self, function: DispatchFunction) -> bool | None:
        return getattr(self, function.value)

    def with_function(self, function: DispatchFunction, enabled: bool) -> DispatchFunctions:
        if not isinstance(enabled, bool):
            raise ValueError("Dispatch function must be on or off")
        return replace(self, **{function.value: enabled})


@dataclass(frozen=True)
class DispatchCommand:
    mode: DispatchMode | None
    power_w: int = 0  # Positive watts charge the battery or export; negative watts discharge or import
    functions: DispatchFunctions = DispatchFunctions()
    soc_min_pct: int = 0
    soc_max_pct: int = 100
    reserve_soc_pct: int | None = None  # 1 percentage point steps
    pv_limit_pct: float | None = None  # 0.01 percentage point steps

    @classmethod
    def battery_charge(cls, power_w: int) -> DispatchCommand:
        if power_w < 0:
            raise ValueError("Charge power must be a non-negative magnitude")
        return cls(DispatchMode.BATTERY_POWER, power_w)

    @classmethod
    def battery_discharge(cls, power_w: int) -> DispatchCommand:
        if power_w < 0:
            raise ValueError("Discharge power must be a non-negative magnitude")
        return cls(DispatchMode.BATTERY_POWER, -power_w)


@dataclass(frozen=True)
class DispatchPeriod:
    enabled: bool | None
    start: _time | None
    end: _time | None
    command: DispatchCommand


@dataclass(frozen=True)
class RegisterWrite:
    """One contiguous block of holding registers to write."""

    address: int
    words: tuple[int, ...]


@dataclass(frozen=True)
class RemoteDispatch:
    capabilities: DispatchCapabilities
    status: DispatchStatus | None = None
    settings: DispatchSettings | None = None
    realtime: DispatchCommand | None = None
    periods: tuple[DispatchPeriod, ...] = ()

    @staticmethod
    def create(input_registers: Sequence[int], holding_registers: Sequence[int]) -> RemoteDispatch:
        """Decode one snapshot. No holding registers are needed for unsupported hardware or versions."""
        capabilities = decode_capabilities(input_registers)
        if not capabilities.known_version:
            return RemoteDispatch(capabilities)

        status_word = input_registers[2] & 0xFFFF
        state = _RUNNING_STATES.get(status_word & 0xFF)
        active_mode = _MODES.get(status_word >> 8) if capabilities.version in (2, 3) else None
        return _decode_holding(holding_registers, capabilities, DispatchStatus(state, active_mode))

    @staticmethod
    def from_registers(
        registers: Mapping[int, int | None], capabilities: DispatchCapabilities
    ) -> RemoteDispatch | None:
        """Decode the holding block from cached registers; None when the layout is unknown or incomplete."""
        if not capabilities.known_version:
            return None
        holding_registers = holding_from_registers(registers)
        if holding_registers is None:
            return None
        return _decode_holding(holding_registers, capabilities, None)

    def period(self, number: int) -> DispatchPeriod:
        if type(number) is not int or not 1 <= number <= len(self.periods):
            raise ValueError(f"Dispatch period {number} is not available")
        return self.periods[number - 1]

    def with_settings(self, settings: DispatchSettings) -> RemoteDispatch:
        return replace(self, settings=settings)

    def with_failsafe_minutes(self, minutes: int) -> RemoteDispatch:
        settings = self._require_settings()
        _validate_failsafe_minutes(minutes)
        return self.with_settings(replace(settings, failsafe_minutes=minutes))

    def with_import_limit_enabled(self, enabled: bool) -> RemoteDispatch:
        settings = self._require_settings()
        _validate_switch(enabled, "Power limit switch")
        return self.with_settings(replace(settings, import_limit=replace(settings.import_limit, enabled=enabled)))

    def with_import_limit_watts(self, watts: int | None) -> RemoteDispatch:
        settings = self._require_settings()
        _validate_limit_watts(watts)
        return self.with_settings(replace(settings, import_limit=replace(settings.import_limit, watts=watts)))

    def with_export_limit_enabled(self, enabled: bool) -> RemoteDispatch:
        settings = self._require_settings()
        _validate_switch(enabled, "Power limit switch")
        return self.with_settings(replace(settings, export_limit=replace(settings.export_limit, enabled=enabled)))

    def with_export_limit_watts(self, watts: int | None) -> RemoteDispatch:
        settings = self._require_settings()
        _validate_limit_watts(watts)
        return self.with_settings(replace(settings, export_limit=replace(settings.export_limit, watts=watts)))

    def _require_settings(self) -> DispatchSettings:
        if self.settings is None:
            raise ValueError("Remote Dispatch settings are not available")
        return self.settings

    def with_realtime(self, command: DispatchCommand) -> RemoteDispatch:
        return replace(self, realtime=command)

    def with_realtime_mode(self, mode: DispatchMode) -> RemoteDispatch:
        command = self._require_realtime()
        _validate_mode(mode, self.capabilities)
        return self.with_realtime(replace(command, mode=mode))

    def with_realtime_power(self, watts: int) -> RemoteDispatch:
        command = self._require_realtime()
        _validate_dispatch_power(watts)
        return self.with_realtime(replace(command, power_w=watts))

    def with_realtime_soc_bounds(self, min_pct: int, max_pct: int) -> RemoteDispatch:
        command = self._require_realtime()
        updated = replace(command, soc_min_pct=min_pct, soc_max_pct=max_pct)
        _validate_soc_bounds(updated)
        return self.with_realtime(updated)

    def with_realtime_reserve_soc(self, pct: int) -> RemoteDispatch:
        command = self._require_realtime()
        _validate_reserve_soc(command, pct, self.capabilities)
        return self.with_realtime(replace(command, reserve_soc_pct=pct))

    def with_realtime_pv_limit(self, pct: float) -> RemoteDispatch:
        command = self._require_realtime()
        _validate_pv_limit(pct, self.capabilities)
        return self.with_realtime(replace(command, pv_limit_pct=pct))

    def with_realtime_function(self, function: DispatchFunction, enabled: bool) -> RemoteDispatch:
        command = self._require_realtime()
        _validate_function(command, function, enabled, self.capabilities)
        return self.with_realtime(replace(command, functions=command.functions.with_function(function, enabled)))

    def with_period(self, number: int, period: DispatchPeriod) -> RemoteDispatch:
        self.period(number)  # Validate before slicing; zero must not address the last period.
        return replace(self, periods=(*self.periods[: number - 1], period, *self.periods[number:]))

    def with_period_enabled(self, number: int, enabled: bool) -> RemoteDispatch:
        period = self.period(number)
        _validate_switch(enabled, "Dispatch period switch")
        if enabled:
            if period.start is None or period.end is None:
                raise ValueError("Set the dispatch period start and end before enabling it")
            _validate_active_command(period.command, self.capabilities)
        return self.with_period(number, replace(period, enabled=enabled))

    def with_period_start(self, number: int, start: _time) -> RemoteDispatch:
        _encode_time(start)
        return self.with_period(number, replace(self.period(number), start=start))

    def with_period_end(self, number: int, end: _time) -> RemoteDispatch:
        _encode_time(end)
        return self.with_period(number, replace(self.period(number), end=end))

    def with_period_mode(self, number: int, mode: DispatchMode) -> RemoteDispatch:
        period = self.period(number)
        _validate_mode(mode, self.capabilities)
        return self.with_period(number, replace(period, command=replace(period.command, mode=mode)))

    def with_period_power(self, number: int, watts: int) -> RemoteDispatch:
        period = self.period(number)
        _validate_dispatch_power(watts)
        return self.with_period(number, replace(period, command=replace(period.command, power_w=watts)))

    def with_period_soc_bounds(self, number: int, min_pct: int, max_pct: int) -> RemoteDispatch:
        period = self.period(number)
        command = replace(period.command, soc_min_pct=min_pct, soc_max_pct=max_pct)
        _validate_soc_bounds(command)
        return self.with_period(number, replace(period, command=command))

    def with_period_reserve_soc(self, number: int, pct: int) -> RemoteDispatch:
        period = self.period(number)
        _validate_reserve_soc(period.command, pct, self.capabilities)
        return self.with_period(number, replace(period, command=replace(period.command, reserve_soc_pct=pct)))

    def with_period_pv_limit(self, number: int, pct: float) -> RemoteDispatch:
        period = self.period(number)
        _validate_pv_limit(pct, self.capabilities)
        return self.with_period(number, replace(period, command=replace(period.command, pv_limit_pct=pct)))

    def with_period_function(self, number: int, function: DispatchFunction, enabled: bool) -> RemoteDispatch:
        period = self.period(number)
        _validate_function(period.command, function, enabled, self.capabilities)
        functions = period.command.functions.with_function(function, enabled)
        return self.with_period(number, replace(period, command=replace(period.command, functions=functions)))

    def _require_realtime(self) -> DispatchCommand:
        if self.realtime is None:
            raise ValueError("Remote Dispatch real-time command is not available")
        return self.realtime


# Solis hybrid protocol Ver3.5, §6.2.1.
INPUT_START = 34502
INPUT_COUNT = 3
HOLDING_START = 44100
HOLDING_COUNT = 100

_CAPABLE = 0xAA55
_SETTINGS_COUNT = 5
_REALTIME_START = 44105
# §6.2.1 says periods 2–6 share period 1's layout, despite the stale reserved labels for their V2/V3 setpoints.
_PERIOD_START = 44116
_PERIOD_STRIDE = 14
_PERIOD_COUNT = 6

_MODE, _POWER_HIGH, _POWER_LOW, _FUNCTIONS, _SOC_MIN, _SOC_MAX, _RESERVE_SOC, _PV_LIMIT = range(8)
_PERIOD_ENABLED, _PERIOD_START_TIME, _PERIOD_END_TIME, _PERIOD_COMMAND = range(4)
_MASTER, _FAILSAFE, _LIMIT_SWITCHES, _IMPORT_LIMIT, _EXPORT_LIMIT = range(_SETTINGS_COUNT)
_IMPORT_ENABLED = 1 << 0
_EXPORT_ENABLED = 1 << 1
_DEFAULT_LIMIT = 0xFFFF
_LIMIT_STEP_W = 100
_POWER_STEP_W = 10
_PV_LIMIT_STEPS_PER_PERCENT = 100

_MODES = {
    1: DispatchMode.BATTERY_HOLD,
    2: DispatchMode.BATTERY_POWER,
    3: DispatchMode.GRID_POWER,
    4: DispatchMode.GRID_PORT_POWER,
    5: DispatchMode.SELF_CONSUMPTION,
    6: DispatchMode.FEED_IN_PRIORITY,
}
_MODE_CODES = {mode: code for code, mode in _MODES.items()}
_RUNNING_STATES = {
    0: DispatchRunningState.STOPPED,
    1: DispatchRunningState.STANDBY,
    2: DispatchRunningState.REALTIME,
    3: DispatchRunningState.SCHEDULED,
}

_PV_SHUTDOWN = 0
_DIGITAL_OUTPUT = 2
_ALLOW_GRID_CHARGE = 4
_OFF_GRID_STANDBY = 6
_BATTERY_RESERVE = 8
_DISABLE_DISCHARGE = 10
_DEMAND_CONTROL = 12
_PV_LIMIT_ENABLED = 14
_PAIR_MASK = 0b11


def decode_capabilities(values: Sequence[int]) -> DispatchCapabilities:
    if len(values) != INPUT_COUNT:
        raise ValueError(f"Expected {INPUT_COUNT} Remote Dispatch input registers")
    supported = (values[0] & 0xFFFF) == _CAPABLE
    return DispatchCapabilities(supported=supported, version=values[1] & 0xFFFF if supported else None)


def holding_from_registers(registers: Mapping[int, int | None]) -> list[int] | None:
    holding_registers = []
    for address in range(HOLDING_START, HOLDING_START + HOLDING_COUNT):
        word = registers.get(address)
        if word is None:
            return None
        holding_registers.append(word & 0xFFFF)
    return holding_registers


def _decode_holding(
    words: Sequence[int], capabilities: DispatchCapabilities, status: DispatchStatus | None
) -> RemoteDispatch:
    if len(words) != HOLDING_COUNT:
        raise ValueError(f"Expected {HOLDING_COUNT} Remote Dispatch holding registers")
    master, failsafe, switches, import_limit, export_limit = _block(words, HOLDING_START, _SETTINGS_COUNT)

    periods = []
    for number in range(1, _PERIOD_COUNT + 1):
        block = _block(words, _period_address(number), _PERIOD_STRIDE)
        periods.append(
            DispatchPeriod(
                _decode_switch(block[_PERIOD_ENABLED]),
                _decode_time(block[_PERIOD_START_TIME]),
                _decode_time(block[_PERIOD_END_TIME]),
                _decode_command(block[_PERIOD_COMMAND:], capabilities),
            )
        )

    return RemoteDispatch(
        capabilities=capabilities,
        status=status,
        settings=DispatchSettings(
            enabled=_decode_switch(master),
            failsafe_minutes=failsafe,
            import_limit=DispatchPowerLimit(bool(switches & _IMPORT_ENABLED), _decode_limit(import_limit)),
            export_limit=DispatchPowerLimit(bool(switches & _EXPORT_ENABLED), _decode_limit(export_limit)),
        ),
        realtime=_decode_command(_block(words, _REALTIME_START, _command_count(capabilities)), capabilities),
        periods=tuple(periods),
    )


def _period_address(number: int) -> int:
    return _PERIOD_START + (number - 1) * _PERIOD_STRIDE


def _block(words: Sequence[int], address: int, count: int) -> list[int]:
    offset = address - HOLDING_START
    # SolisCloud can return signed 16-bit register words, even for U16 fields.
    return [word & 0xFFFF for word in words[offset : offset + count]]


def _decode_switch(word: int) -> bool | None:
    return bool(word) if word in (0, 1) else None


def _decode_time(word: int) -> _time | None:
    hour, minute = word >> 8, word & 0xFF
    return _time(hour, minute) if hour < 24 and minute < 60 else None


def _decode_limit(word: int) -> int | None:
    return None if word == _DEFAULT_LIMIT else word * _LIMIT_STEP_W


def _command_count(capabilities: DispatchCapabilities) -> int:
    if capabilities.supports_pv_limit:
        return _PV_LIMIT + 1
    if capabilities.supports_battery_reserve:
        return _RESERVE_SOC + 1
    return _SOC_MAX + 1


def _decode_command(words: Sequence[int], capabilities: DispatchCapabilities) -> DispatchCommand:
    functions = words[_FUNCTIONS]

    def directive(shift: int, *, true_code: int = 2) -> bool | None:
        code = (functions >> shift) & _PAIR_MASK
        return code == true_code if code in (1, 2) else None

    return DispatchCommand(
        mode=_MODES.get(words[_MODE]),
        power_w=_modbus.unpack_s32(words[_POWER_HIGH], words[_POWER_LOW]) * _POWER_STEP_W,
        functions=DispatchFunctions(
            pv_shutdown=directive(_PV_SHUTDOWN),
            digital_output_closed=directive(_DIGITAL_OUTPUT),
            allow_grid_charge=directive(_ALLOW_GRID_CHARGE, true_code=1),
            off_grid_battery_standby=directive(_OFF_GRID_STANDBY),
            battery_reserve_enabled=directive(_BATTERY_RESERVE) if capabilities.supports_battery_reserve else None,
            disable_discharge=directive(_DISABLE_DISCHARGE) if capabilities.supports_discharge_prohibition else None,
            demand_control_enabled=directive(_DEMAND_CONTROL) if capabilities.supports_demand_control else None,
            pv_limit_enabled=directive(_PV_LIMIT_ENABLED) if capabilities.supports_pv_limit else None,
        ),
        soc_min_pct=words[_SOC_MIN],
        soc_max_pct=words[_SOC_MAX],
        reserve_soc_pct=words[_RESERVE_SOC] if capabilities.supports_battery_reserve else None,
        pv_limit_pct=words[_PV_LIMIT] / _PV_LIMIT_STEPS_PER_PERCENT if capabilities.supports_pv_limit else None,
    )


def _encode_functions(
    word: int, before: DispatchFunctions, after: DispatchFunctions, capabilities: DispatchCapabilities
) -> int:
    def change(shift: int, old: bool | None, new: bool | None, *, true_code: int = 2, supported: bool = True) -> None:
        nonlocal word
        if old == new:
            return
        if not supported:
            raise ValueError("Dispatch function is not supported by this inverter version")
        if not isinstance(new, bool):
            # Codes 0 and 3 are ignored by the inverter, not a way to clear a switch.
            raise ValueError("Set the dispatch function explicitly to on or off")
        code = true_code if new else 3 - true_code
        word = (word & ~(_PAIR_MASK << shift)) | (code << shift)

    change(_PV_SHUTDOWN, before.pv_shutdown, after.pv_shutdown)
    change(_DIGITAL_OUTPUT, before.digital_output_closed, after.digital_output_closed)
    change(_ALLOW_GRID_CHARGE, before.allow_grid_charge, after.allow_grid_charge, true_code=1)
    change(_OFF_GRID_STANDBY, before.off_grid_battery_standby, after.off_grid_battery_standby)
    change(
        _BATTERY_RESERVE,
        before.battery_reserve_enabled,
        after.battery_reserve_enabled,
        supported=capabilities.supports_battery_reserve,
    )
    change(
        _DISABLE_DISCHARGE,
        before.disable_discharge,
        after.disable_discharge,
        supported=capabilities.supports_discharge_prohibition,
    )
    change(
        _DEMAND_CONTROL,
        before.demand_control_enabled,
        after.demand_control_enabled,
        supported=capabilities.supports_demand_control,
    )
    change(_PV_LIMIT_ENABLED, before.pv_limit_enabled, after.pv_limit_enabled, supported=capabilities.supports_pv_limit)
    return word


def _validate_soc_bounds(command: DispatchCommand) -> None:
    low, high = command.soc_min_pct, command.soc_max_pct
    if type(low) is not int or type(high) is not int or not 0 <= low < high <= 100:
        raise ValueError("Dispatch SOC bounds must be whole percentages with 0 <= min < max <= 100")


def _encode_command(
    words: list[int], before: DispatchCommand, after: DispatchCommand, capabilities: DispatchCapabilities
) -> list[int]:
    if before.mode != after.mode:
        if not isinstance(after.mode, DispatchMode) or after.mode not in capabilities.supported_modes:
            raise ValueError("Unsupported Remote Dispatch mode")
        words[_MODE] = _MODE_CODES[after.mode]
    if before.power_w != after.power_w:
        words[_POWER_HIGH], words[_POWER_LOW] = _modbus.pack_s32(
            _encode_watts(after.power_w, _POWER_STEP_W, -(1 << 31), (1 << 31) - 1)
        )
    words[_FUNCTIONS] = _encode_functions(words[_FUNCTIONS], before.functions, after.functions, capabilities)
    bounds_changed = (before.soc_min_pct, before.soc_max_pct) != (after.soc_min_pct, after.soc_max_pct)
    if bounds_changed:
        _validate_soc_bounds(after)
        words[_SOC_MIN], words[_SOC_MAX] = after.soc_min_pct, after.soc_max_pct

    reserve_changed = before.reserve_soc_pct != after.reserve_soc_pct
    if reserve_changed or (
        after.functions.battery_reserve_enabled and (bounds_changed or not before.functions.battery_reserve_enabled)
    ):
        if not capabilities.supports_battery_reserve:
            raise ValueError("Battery reserve requires Remote Dispatch V2 or V3")
        reserve = after.reserve_soc_pct
        # The lower hardware limit (over-discharge SOC) is outside the dispatch registers.
        if type(reserve) is not int or not 0 <= reserve <= after.soc_max_pct:
            raise ValueError("Battery reserve SOC must be a whole percentage up to the SOC ceiling")
        if reserve_changed:
            words[_RESERVE_SOC] = reserve

    if before.pv_limit_pct != after.pv_limit_pct or (
        after.functions.pv_limit_enabled and not before.functions.pv_limit_enabled
    ):
        if not capabilities.supports_pv_limit:
            raise ValueError("PV limiting requires Remote Dispatch V3")
        percent = after.pv_limit_pct
        if percent is None or not 0 <= percent <= 100 or percent != round(percent, 2):
            raise ValueError("PV limit must be 0 to 100% in 0.01% steps")
        words[_PV_LIMIT] = round(percent * _PV_LIMIT_STEPS_PER_PERCENT)
    return words


def _encode_watts(watts: int, step: int, minimum: int, maximum: int) -> int:
    if type(watts) is not int or watts % step or not minimum <= watts // step <= maximum:
        raise ValueError(f"Power must be {minimum * step} to {maximum * step} W in {step} W steps")
    return watts // step


def _validate_failsafe_minutes(minutes: int) -> None:
    if type(minutes) is not int or not 1 <= minutes <= 1440:
        raise ValueError("Dispatch failsafe must be 1 to 1440 whole minutes")


def _validate_switch(value: bool, name: str) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be on or off")


def _validate_limit_watts(watts: int | None) -> None:
    if watts is not None:
        _encode_watts(watts, _LIMIT_STEP_W, 0, _DEFAULT_LIMIT - 1)


def _validate_mode(mode: DispatchMode, capabilities: DispatchCapabilities) -> None:
    if not isinstance(mode, DispatchMode) or mode not in capabilities.supported_modes:
        raise ValueError("Unsupported Remote Dispatch mode")


def _validate_dispatch_power(watts: int) -> None:
    _encode_watts(watts, _POWER_STEP_W, -(1 << 31), (1 << 31) - 1)


def _validate_reserve_soc(command: DispatchCommand, pct: int, capabilities: DispatchCapabilities) -> None:
    if not capabilities.supports_battery_reserve:
        raise ValueError("Battery reserve requires Remote Dispatch V2 or V3")
    if type(pct) is not int or not 0 <= pct <= command.soc_max_pct:
        raise ValueError("Battery reserve SOC must be a whole percentage up to the SOC ceiling")


def _validate_pv_limit(pct: float, capabilities: DispatchCapabilities) -> None:
    if not capabilities.supports_pv_limit:
        raise ValueError("PV limiting requires Remote Dispatch V3")
    if type(pct) not in (int, float) or not 0 <= pct <= 100 or pct != round(pct, 2):
        raise ValueError("PV limit must be 0 to 100% in 0.01% steps")


_RESERVE_FUNCTIONS = frozenset(
    {
        DispatchFunction.BATTERY_RESERVE_ENABLED,
        DispatchFunction.DISABLE_DISCHARGE,
        DispatchFunction.DEMAND_CONTROL_ENABLED,
    }
)


def _validate_function(
    command: DispatchCommand,
    function: DispatchFunction,
    enabled: bool,
    capabilities: DispatchCapabilities,
) -> None:
    if not isinstance(function, DispatchFunction):
        raise ValueError("Unknown dispatch function")
    _validate_switch(enabled, "Dispatch function")
    if function in _RESERVE_FUNCTIONS and not capabilities.supports_battery_reserve:
        raise ValueError("Dispatch function is not supported by this inverter version")
    if function == DispatchFunction.PV_LIMIT_ENABLED and not capabilities.supports_pv_limit:
        raise ValueError("Dispatch function is not supported by this inverter version")
    if enabled and function == DispatchFunction.BATTERY_RESERVE_ENABLED and command.reserve_soc_pct is None:
        raise ValueError("Set battery reserve SOC before enabling it")
    if enabled and function == DispatchFunction.PV_LIMIT_ENABLED and command.pv_limit_pct is None:
        raise ValueError("Set PV limit before enabling it")


def _encode_settings(words: list[int], before: DispatchSettings, after: DispatchSettings) -> list[int]:
    if before.enabled != after.enabled:
        raise ValueError("Use the start or stop operation to change the master switch")
    if before.failsafe_minutes != after.failsafe_minutes:
        _validate_failsafe_minutes(after.failsafe_minutes)
        words[_FAILSAFE] = after.failsafe_minutes

    def change_limit(old: DispatchPowerLimit, new: DispatchPowerLimit, flag: int, register: int) -> None:
        if old.enabled != new.enabled:
            if not isinstance(new.enabled, bool):
                raise ValueError("Power limit switch must be on or off")
            words[_LIMIT_SWITCHES] = words[_LIMIT_SWITCHES] | flag if new.enabled else words[_LIMIT_SWITCHES] & ~flag
        if old.watts != new.watts:
            words[register] = (
                _DEFAULT_LIMIT if new.watts is None else _encode_watts(new.watts, _LIMIT_STEP_W, 0, _DEFAULT_LIMIT - 1)
            )

    change_limit(before.import_limit, after.import_limit, _IMPORT_ENABLED, _IMPORT_LIMIT)
    change_limit(before.export_limit, after.export_limit, _EXPORT_ENABLED, _EXPORT_LIMIT)
    return words


def _encode_time(value: _time | None) -> int:
    if not isinstance(value, _time) or value.tzinfo is not None or value.second or value.microsecond:
        raise ValueError("Dispatch time must be an inverter-local time in whole minutes")
    return (value.hour << 8) | value.minute


def _validate_active_command(command: DispatchCommand, capabilities: DispatchCapabilities) -> None:
    if command.mode not in capabilities.supported_modes:
        raise ValueError("Set a supported mode before activating the dispatch command")
    _validate_soc_bounds(command)


def _encode_period(
    words: list[int], before: DispatchPeriod, after: DispatchPeriod, capabilities: DispatchCapabilities
) -> list[int]:
    if before.enabled != after.enabled:
        if not isinstance(after.enabled, bool):
            raise ValueError("Dispatch period switch must be on or off")
        if after.enabled:
            _encode_time(after.start)
            _encode_time(after.end)
            _validate_active_command(after.command, capabilities)
        words[_PERIOD_ENABLED] = int(after.enabled)
    if before.start != after.start:
        words[_PERIOD_START_TIME] = _encode_time(after.start)
    if before.end != after.end:
        words[_PERIOD_END_TIME] = _encode_time(after.end)
    words[_PERIOD_COMMAND:] = _encode_command(words[_PERIOD_COMMAND:], before.command, after.command, capabilities)
    return words


def encode_changes(before: RemoteDispatch, after: RemoteDispatch, holding: Sequence[int]) -> list[RegisterWrite]:
    """Prepare and validate all changed blocks before sending any of them."""
    if not before.capabilities.known_version or before.settings is None or before.realtime is None:
        raise ValueError("Unsupported Remote Dispatch version")
    if (
        after.capabilities != before.capabilities
        or after.status != before.status
        or after.settings is None
        or after.realtime is None
        or len(after.periods) != _PERIOD_COUNT
    ):
        raise ValueError("Only Remote Dispatch settings, real-time command and periods can be edited")

    writes: list[RegisterWrite] = []
    capabilities = before.capabilities
    command_count = _command_count(capabilities)
    if before.settings != after.settings:
        block = _block(holding, HOLDING_START, _SETTINGS_COUNT)
        writes.append(RegisterWrite(HOLDING_START, tuple(_encode_settings(block, before.settings, after.settings))))
    if before.realtime != after.realtime:
        writes.append(_encode_realtime(before, after.realtime, holding))
    for number, (old, new) in enumerate(zip(before.periods, after.periods, strict=True), start=1):
        if old != new:
            address = _period_address(number)
            block = _block(holding, address, _PERIOD_COMMAND + command_count)
            writes.append(RegisterWrite(address, tuple(_encode_period(block, old, new, capabilities))))
    return writes


def apply_writes(registers: Mapping[int, int | None], writes: Sequence[RegisterWrite]) -> dict[int, int | None]:
    updated = dict(registers)
    for write in writes:
        for offset, word in enumerate(write.words):
            updated[write.address + offset] = word
    return updated


def encode_start(before: RemoteDispatch, holding: Sequence[int]) -> RegisterWrite:
    settings = before.settings
    if settings is None or not 1 <= settings.failsafe_minutes <= 1440:
        raise ValueError("Set a valid dispatch failsafe before enabling Remote Dispatch")
    block = _block(holding, HOLDING_START, _SETTINGS_COUNT)
    block[_MASTER] = 1
    return RegisterWrite(HOLDING_START, tuple(block))


def _encode_realtime(
    before: RemoteDispatch, command: DispatchCommand, holding: Sequence[int], *, activate: bool = False
) -> RegisterWrite:
    if before.realtime is None:
        raise ValueError("No real-time dispatch command available")
    capabilities = before.capabilities
    if activate:
        _validate_active_command(command, capabilities)
    block = _block(holding, _REALTIME_START, _command_count(capabilities))
    return RegisterWrite(_REALTIME_START, tuple(_encode_command(block, before.realtime, command, capabilities)))


def encode_stop(holding: Sequence[int]) -> RegisterWrite:
    block = _block(holding, HOLDING_START, _SETTINGS_COUNT)
    block[_MASTER] = 0
    return RegisterWrite(HOLDING_START, tuple(block))
