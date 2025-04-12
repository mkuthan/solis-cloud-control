from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry

from custom_components.solis_cloud_control.coordinator import SolisCloudControlCoordinator


@dataclass
class SolisCloudControlData:
    coordinator: SolisCloudControlCoordinator

class SolisCloudControlConfigEntry(ConfigEntry[SolisCloudControlData]):
    pass

