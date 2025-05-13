import asyncio
import json
import logging
import os

import aiohttp

from custom_components.solis_cloud_control.api.solis_api import SolisCloudControlApiClient
from custom_components.solis_cloud_control.const import API_BASE_URL


async def read_batch(client: SolisCloudControlApiClient, inverter_sn: str) -> None:
    cids_to_read = [56, 636]

    result = await client.read_batch(inverter_sn, cids_to_read)
    sorted_items = sorted(result.items(), key=lambda item: int(str(item[0])))
    sorted_result_for_json = dict(sorted_items)
    print(json.dumps(sorted_result_for_json, indent=2))


#
# uv run -m scripts.api_tester
#
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

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
            await read_batch(client, inverter_sn)

    asyncio.run(_run_script())
