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
