from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient

# https://github.com/Pho3niX90/solis_modbus/blame/master/custom_components/solis_modbus/__init__.py
# https://developer.soliscloud.com/guide/device-control-v1.html#interface-overview
# https://developer.soliscloud.com/guide/modbus.html
# https://developer.soliscloud.com/guide/modbus-grid-tied.html
# https://developer.soliscloud.com/guide/modbus-storage.html

BLOCK1_REG: int = 44100
BLOCK2_REG: int = 44105


# requires V2
# gated by 44108 BIT08-09
# DISPATCH_RESERVE_SOC_REG = 44111

# requires V3
# 0.01 %, gated by 44108 BIT14-15
# DISPATCH_PV_LIMIT_REG = 44112

# 44113 - 44115 - unused


class DispatchMode(Enum):
    BATTERY_HOLD = (1, 0)
    BATTERY_CHARGE = (2, 1)
    BATTERY_DISCHARGE = (2, -1)
    GRID_IMPORT = (3, -1)
    GRID_EXPORT = (3, 1)
    GRID_PORT_IMPORT = (4, -1)
    GRID_PORT_EXPORT = (4, 1)
    SELF_CONSUMPTION = (5, 0)  # requires V2
    FEED_IN_PRIORITY = (6, 0)  # requires V2

    @property
    def mode(self) -> int:
        return self.value[0]

    @property
    def sign(self) -> int:
        return self.value[1]


@dataclass(frozen=True)
class DispatchFunction:
    pv_shutdown: bool | None = None
    allow_grid_charge: bool | None = None
    disable_discharge: bool | None = None

    @property
    def value(self) -> int:
        def pair(value: bool | None, true_code: int, false_code: int) -> int:
            return 0 if value is None else (true_code if value else false_code)

        return (
            pair(self.pv_shutdown, 2, 1)
            | pair(self.allow_grid_charge, 1, 2) << 4
            | pair(self.disable_discharge, 2, 1) << 10
        )


async def dispatch_version(api_client: SolisCloudControlApiClient, inverter_sn: str) -> int | None:
    cap = await api_client.read_register(inverter_sn, 34502, "04")
    if int(cap) & 0xFFFF != 0xAA55:  # atRead may return it signed, e.g. "-21931"
        return None
    return int(await api_client.read_register(inverter_sn, 34503, "04"))  # 1, 2 or 3


async def dispatch(
    api_client: SolisCloudControlApiClient,
    inverter_sn: str,
    mode: DispatchMode,
    failsafe_min: int = 30,
    import_limit_w: int | None = None,
    export_limit_w: int | None = None,
    power_w: int = 0,
    function: DispatchFunction | None = None,
    soc_min: int = 0,
    soc_max: int = 100,
) -> None:
    switches = (import_limit_w is not None) | (export_limit_w is not None) << 1

    block1 = [1, failsafe_min, switches, _limit(import_limit_w), _limit(export_limit_w)]

    if function is None:
        function = DispatchFunction()

    block2 = [mode.mode, *_s32(mode.sign * round(power_w / 10)), function.value, soc_min, soc_max]

    await api_client.control_at_command(inverter_sn, _build_write_multiple_frame(BLOCK1_REG, block1))
    await api_client.control_at_command(inverter_sn, _build_write_multiple_frame(BLOCK2_REG, block2))


async def dispatch_schedule(
    api_client: SolisCloudControlApiClient,
    inverter_sn: str,
    period: int,
    start: str,
    end: str,
    mode: DispatchMode,
    power_w: int = 0,
    function: DispatchFunction | None = None,
    soc_min: int = 0,
    soc_max: int = 100,
    enabled: bool = True,
    failsafe_min: int = 1440,
) -> None:
    if function is None:
        function = DispatchFunction()

    base = 44116 + (period - 1) * 14
    block = [
        int(enabled),
        _hhmm(start),
        _hhmm(end),
        mode.mode,
        *_s32(mode.sign * round(power_w / 10)),
        function.value,
        soc_min,
        soc_max,
    ]
    await api_client.control_at_command(inverter_sn, _build_write_multiple_frame(base, block))

    if enabled:
        block1 = [1, failsafe_min]
        await api_client.control_at_command(inverter_sn, _build_write_multiple_frame(BLOCK1_REG, block1))


async def dispatch_stop(api_client: SolisCloudControlApiClient, inverter_sn: str) -> None:
    # TODO: why 44105 and 44108? 44100 -> 0 should be enough
    # for addr, val in ((44105, 1), (44108, 1), (44100, 0)):
    #     await api_client.control_at_command(inverter_sn, _build_write_multiple_frame(addr, [val]))
    await api_client.control_at_command(inverter_sn, _build_write_multiple_frame(44100, [0]))


def _limit(watts: int | None) -> int:
    return 0xFFFF if watts is None else (watts + 50) // 100


def _s32(v: int) -> list[int]:
    raw = v & 0xFFFFFFFF
    return [raw >> 16, raw & 0xFFFF]


def _hhmm(s: str) -> int:
    h, m = map(int, s.split(":"))
    return h << 8 | m


def _build_write_multiple_frame(start: int, values: list[int], slave: int = 1) -> str:
    regs = [v & 0xFFFF for v in values]
    frame = [slave, 0x10, start >> 8, start & 0xFF, len(regs) >> 8, len(regs) & 0xFF, len(regs) * 2]
    for r in regs:
        frame += [r >> 8, r & 0xFF]

    crc = _crc16_modbus(frame)
    frame += [crc & 0xFF, crc >> 8]  # Append low byte first, then high byte

    return " ".join(f"{b:02X}" for b in frame)


def _crc16_modbus(data: list[int]) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc
