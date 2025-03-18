from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.loader import Integration

from .api import SolisCloudControlApiClient
from .coordinator import SolisCloudControlDataUpdateCoordinator


type SolisCloudControlConfigEntry = ConfigEntry[SolisCloudControlData]


@dataclass
class SolisCloudControlData:
    client: SolisCloudControlApiClient
    coordinator: SolisCloudControlDataUpdateCoordinator
    integration: Integration
