from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

if TYPE_CHECKING:
    from custom_components.solis_cloud_control.coordinator import SolisCloudControlCoordinator
    from custom_components.solis_cloud_control.inverters.inverter import Inverter


@dataclass
class SolisCloudControlData:
    inverter: Inverter
    coordinator: SolisCloudControlCoordinator


class SolisCloudControlConfigEntry(ConfigEntry[SolisCloudControlData]):
    pass
