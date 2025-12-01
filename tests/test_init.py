from collections import Counter
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_API_KEY, CONF_API_TOKEN, CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solis_cloud_control import async_migrate_entry
from custom_components.solis_cloud_control.const import CONF_INVERTER_SN, DOMAIN
from custom_components.solis_cloud_control.inverters.inverter import Inverter


async def test_async_setup_entry(hass, mock_api_client, mock_config_entry, any_inverter):
    read_batch_cids = dict.fromkeys(any_inverter.read_batch_cids, "0")

    for cid in [any_inverter.on_off.on_cid, any_inverter.on_off.off_cid]:
        read_batch_cids[cid] = "190"

    for cid in [
        any_inverter.charge_discharge_slots.charge_slot1.time_cid,
        any_inverter.charge_discharge_slots.charge_slot2.time_cid,
        any_inverter.charge_discharge_slots.charge_slot3.time_cid,
        any_inverter.charge_discharge_slots.charge_slot4.time_cid,
        any_inverter.charge_discharge_slots.charge_slot5.time_cid,
        any_inverter.charge_discharge_slots.charge_slot6.time_cid,
        any_inverter.charge_discharge_slots.discharge_slot1.time_cid,
        any_inverter.charge_discharge_slots.discharge_slot2.time_cid,
        any_inverter.charge_discharge_slots.discharge_slot3.time_cid,
        any_inverter.charge_discharge_slots.discharge_slot4.time_cid,
        any_inverter.charge_discharge_slots.discharge_slot5.time_cid,
        any_inverter.charge_discharge_slots.discharge_slot6.time_cid,
    ]:
        read_batch_cids[cid] = "00:00-00:00"

    mock_api_client.read_batch.return_value = read_batch_cids

    charge_discharge_settings = "0,0,00:00,00:00,00:00,00:00,0,0,00:00,00:00,00:00,00:00,0,0,00:00,00:00,00:00,00:00"

    mock_api_client.read.side_effect = lambda inverter_sn, cid, max_retry_time: (  # noqa: ARG005
        charge_discharge_settings if cid == 103 else None
    )

    with (
        patch(
            "custom_components.solis_cloud_control._create_api_client",
            return_value=mock_api_client,
        ),
        patch(
            "custom_components.solis_cloud_control.create_inverter_info",
            return_value=any_inverter.info,
        ),
        patch(
            "custom_components.solis_cloud_control.create_inverter",
            return_value=any_inverter,
        ),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # check if the config entry is loaded
    assert mock_config_entry.state is ConfigEntryState.LOADED

    # coordinator.async_config_entry_first_refresh()
    assert mock_api_client.read_batch.called

    assert hasattr(mock_config_entry, "runtime_data")
    assert mock_config_entry.runtime_data.coordinator is not None
    assert mock_config_entry.runtime_data.inverter is not None

    # check device registration
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(identifiers={(DOMAIN, any_inverter.info.serial_number)})

    assert device is not None
    assert device.manufacturer == "Solis"
    assert device.name == f"Inverter Control {any_inverter.info.serial_number}"
    assert device.model_id == any_inverter.info.model
    assert device.model == any_inverter.info.machine
    assert device.sw_version == any_inverter.info.version

    # check entity registration
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, mock_config_entry.entry_id)

    platform_counts = Counter(entry.domain for entry in entries)
    assert platform_counts[Platform.NUMBER] == 40
    assert platform_counts[Platform.SELECT] == 1
    assert platform_counts[Platform.SENSOR] == 7
    assert platform_counts[Platform.SWITCH] == 17
    assert platform_counts[Platform.TEXT] == 18

    platform_disabled_counts = Counter(entry.domain for entry in entries if entry.disabled_by is not None)
    assert platform_disabled_counts[Platform.NUMBER] == 0
    assert platform_disabled_counts[Platform.SELECT] == 0
    assert platform_disabled_counts[Platform.SENSOR] == 7
    assert platform_disabled_counts[Platform.SWITCH] == 0
    assert platform_disabled_counts[Platform.TEXT] == 0


async def test_async_setup_entry_undefined_inverter(hass, mock_api_client, mock_config_entry, any_inverter_info):
    undefined_inverter = Inverter(info=any_inverter_info)

    with (
        patch(
            "custom_components.solis_cloud_control._create_api_client",
            return_value=mock_api_client,
        ),
        patch(
            "custom_components.solis_cloud_control.create_inverter_info",
            return_value=undefined_inverter.info,
        ),
        patch(
            "custom_components.solis_cloud_control.create_inverter",
            return_value=undefined_inverter,
        ),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # check entity registration
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, mock_config_entry.entry_id)
    assert len(entries) == 0


async def test_migrate_config_entry_v1_to_v2(hass: HomeAssistant):
    config_entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
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
