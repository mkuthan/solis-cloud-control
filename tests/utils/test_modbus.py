import pytest

from custom_components.solis_cloud_control.utils.modbus import build_write_registers_frame, pack_s32, to_u16, unpack_s32


@pytest.mark.parametrize(("value", "words"), [(0, (0, 0)), (-300, (0xFFFF, 0xFED4)), (0x12345678, (0x1234, 0x5678))])
def test_signed_word_pair(value: int, words: tuple[int, int]) -> None:
    assert pack_s32(value) == words
    assert unpack_s32(*words) == value


@pytest.mark.parametrize(("word", "expected"), [(0, 0), (0xAA55, 0xAA55), (-21931, 0xAA55), (-1, 0xFFFF)])
def test_to_u16(word: int, expected: int) -> None:
    assert to_u16(word) == expected


def test_write_registers_frame_matches_solis_example() -> None:
    assert (
        build_write_registers_frame(44100, [1, 5, 0, 0, 0])
        == "01 10 AC 44 00 05 0A 00 01 00 05 00 00 00 00 00 00 B1 51"
    )
