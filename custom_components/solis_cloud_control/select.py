from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .entity import StorageModeEntity

SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Solis Cloud Control select platform."""
    if discovery_info is None:
        return

    client = discovery_info["client"]
    inverter_sn = discovery_info["inverter_sn"]

    entities = [StorageModeEntity(hass, client, inverter_sn)]
    async_add_entities(entities, True)
