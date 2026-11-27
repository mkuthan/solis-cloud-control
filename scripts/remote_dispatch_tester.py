import asyncio
import logging
import os

import aiohttp

from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient
from custom_components.solis_cloud_control.const import API_BASE_URL
from custom_components.solis_cloud_control.domain import remote_dispatch
from custom_components.solis_cloud_control.utils.modbus import build_write_registers_frame

#
# uv run -m scripts.remote_dispatch_tester
#
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    api_key = os.environ.get("SOLIS_API_KEY", "your_api_key")
    api_secret = os.environ.get("SOLIS_API_SECRET", "your_api_secret")
    inverter_sn = os.environ.get("SOLIS_INVERTER_SN", "your_inverter_sn")

    async def _run_script() -> None:
        async with aiohttp.ClientSession() as session:
            client = SolisCloudControlApiClient(
                base_url=API_BASE_URL,
                api_key=api_key,
                api_token=api_secret,
                session=session,
            )

            input_registers = await client.read_registers(
                inverter_sn,
                remote_dispatch.INPUT_START,
                function_code="04",
                register_number=remote_dispatch.INPUT_COUNT,
            )

            capabilities = remote_dispatch.decode_capabilities(input_registers)
            holding_registers = []
            if capabilities.known_version:
                holding_registers = await client.read_registers(
                    inverter_sn,
                    remote_dispatch.HOLDING_START,
                    function_code="03",
                    register_number=remote_dispatch.HOLDING_COUNT,
                )

            dispatch = remote_dispatch.RemoteDispatch.create(input_registers, holding_registers)
            print(f"Version: {dispatch.capabilities.version}")

            if dispatch.capabilities.known_version:
                write = remote_dispatch.encode_stop(holding_registers)
                frame = build_write_registers_frame(write.address, write.words)
                await client.control_at_command(inverter_sn, frame)

    asyncio.run(_run_script())
