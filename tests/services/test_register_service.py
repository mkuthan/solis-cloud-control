from dataclasses import replace
from typing import TYPE_CHECKING
from unittest.mock import call

import pytest

from custom_components.solis_cloud_control.api.solis_api_error import SolisCloudControlApiError
from custom_components.solis_cloud_control.domain.remote_dispatch import RegisterWrite
from custom_components.solis_cloud_control.services.register_service import RegisterService, RegisterServiceError
from custom_components.solis_cloud_control.utils.modbus import build_write_registers_frame

if TYPE_CHECKING:
    from unittest.mock import AsyncMock

    from custom_components.solis_cloud_control.inverters.inverter import Inverter

_SERIAL = "any_inverter_sn"


def _read_kwargs(function_code: str, count: int) -> dict:
    return {"function_code": function_code, "register_number": count, "max_retry_time": 60}


@pytest.fixture
def register_service(mock_api_client: AsyncMock, any_inverter: Inverter) -> RegisterService:
    return RegisterService(mock_api_client, any_inverter)


async def test_read_all_reads_holding(register_service: RegisterService, mock_api_client: AsyncMock) -> None:
    mock_api_client.read_registers.side_effect = lambda _serial, register, **kw: [
        register + i for i in range(kw["register_number"])
    ]

    registers = await register_service.read_all()

    assert mock_api_client.read_registers.await_args_list == [
        call(_SERIAL, 44100, **_read_kwargs("03", 100)),
    ]
    assert sorted(registers) == [*range(44100, 44200)]
    assert registers[44100] == 44100
    assert registers[44199] == (44199 & 0xFFFF)


async def test_read_all_normalizes_signed_words(register_service: RegisterService, mock_api_client: AsyncMock) -> None:
    mock_api_client.read_registers.side_effect = lambda _serial, _register, **kw: [-1] * kw["register_number"]

    registers = await register_service.read_all()

    assert registers[44100] == 0xFFFF
    assert registers[44199] == 0xFFFF


async def test_read_all_does_not_probe_capability(
    register_service: RegisterService, mock_api_client: AsyncMock
) -> None:
    # Feature detection happens once in the inverter factory, a layout means the feature is supported
    mock_api_client.read_registers.return_value = [0] * 100

    registers = await register_service.read_all()

    assert mock_api_client.read_registers.await_count == 1
    assert len(registers) == 100


async def test_read_all_without_remote_dispatch(mock_api_client: AsyncMock, any_inverter: Inverter) -> None:
    service = RegisterService(mock_api_client, replace(any_inverter, remote_dispatch_master=None))

    assert await service.read_all() == {}
    mock_api_client.read_registers.assert_not_awaited()


async def test_read_all_api_error(register_service: RegisterService, mock_api_client: AsyncMock) -> None:
    mock_api_client.read_registers.side_effect = SolisCloudControlApiError("any error")

    with pytest.raises(RegisterServiceError, match="any error"):
        await register_service.read_all()


async def test_write_sends_full_block(register_service: RegisterService, mock_api_client: AsyncMock) -> None:
    write = RegisterWrite(44100, (1, 5, 0x8001, 0xFFFF, 0))

    await register_service.write([write])

    mock_api_client.control_at_command.assert_awaited_once_with(
        _SERIAL, build_write_registers_frame(44100, write.words)
    )
    mock_api_client.read_registers.assert_not_awaited()


async def test_write_sends_multiple_blocks_in_order(
    register_service: RegisterService, mock_api_client: AsyncMock
) -> None:
    writes = [
        RegisterWrite(44100, (1, 5, 0, 0, 0)),
        RegisterWrite(44105, (2, 0, 0, 0, 10, 90)),
    ]

    await register_service.write(writes)

    assert mock_api_client.control_at_command.await_args_list == [
        call(_SERIAL, build_write_registers_frame(44100, writes[0].words)),
        call(_SERIAL, build_write_registers_frame(44105, writes[1].words)),
    ]


async def test_write_does_nothing_without_blocks(register_service: RegisterService, mock_api_client: AsyncMock) -> None:
    await register_service.write([])

    mock_api_client.control_at_command.assert_not_awaited()


async def test_write_api_error(register_service: RegisterService, mock_api_client: AsyncMock) -> None:
    mock_api_client.control_at_command.side_effect = SolisCloudControlApiError("any error")

    with pytest.raises(RegisterServiceError, match="any error"):
        await register_service.write([RegisterWrite(44100, (0,))])
