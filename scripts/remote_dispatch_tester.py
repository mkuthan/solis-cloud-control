import asyncio
import logging
import os

import aiohttp

from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient
from custom_components.solis_cloud_control.const import API_BASE_URL
from custom_components.solis_cloud_control.remote_dispatch.remote_dispatch_service import (
    dispatch_stop,
    dispatch_version,
)

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
            version = await dispatch_version(client, inverter_sn)
            print(f"Version: {version}")

            if version is not None:
                await dispatch_stop(client, inverter_sn)

    asyncio.run(_run_script())
