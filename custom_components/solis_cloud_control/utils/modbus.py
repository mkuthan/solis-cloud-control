"""Pure Modbus word and RTU frame helpers."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


def to_u16(word: int) -> int:
    return word & 0xFFFF


def unpack_s32(high: int, low: int) -> int:
    raw = high << 16 | low
    return raw - (1 << 32) if raw & (1 << 31) else raw


def pack_s32(value: int) -> tuple[int, int]:
    raw = value.to_bytes(4, "big", signed=True)
    return int.from_bytes(raw[:2], "big"), int.from_bytes(raw[2:], "big")


def build_write_registers_frame(address: int, words: Sequence[int], slave: int = 1) -> str:
    if not 1 <= len(words) <= 123:
        raise ValueError("FC16 requires between 1 and 123 register words")
    frame = bytearray((slave, 0x10))
    frame.extend(address.to_bytes(2, "big"))
    frame.extend(len(words).to_bytes(2, "big"))
    frame.append(2 * len(words))
    for word in words:
        frame.extend(word.to_bytes(2, "big"))
    frame.extend(_crc16_modbus(frame).to_bytes(2, "little"))
    return frame.hex(" ").upper()


def _crc16_modbus(payload: bytes | bytearray) -> int:
    crc = 0xFFFF
    for byte in payload:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc
