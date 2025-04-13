import pytest
from homeassistant.const import CONF_API_KEY, CONF_API_TOKEN, CONF_TOKEN
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solis_cloud_control import async_migrate_entry
from custom_components.solis_cloud_control.const import CONF_INVERTER_SN, DOMAIN


async def test_migrate_config_entry_v1_to_v2(hass: HomeAssistant):
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        data={
            CONF_API_KEY: "any api key",
            CONF_TOKEN: "any api token",
            CONF_INVERTER_SN: "any inverter sn",
        },
    )
    config_entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, config_entry)

    assert config_entry.version == 2

    assert CONF_TOKEN not in config_entry.data
    assert CONF_API_TOKEN in config_entry.data
