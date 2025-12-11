import logging
from datetime import datetime

from homeassistant.components.datetime import DateTimeEntity, DateTimeEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry
from custom_components.solis_cloud_control.inverters.inverter import InverterTime
from custom_components.solis_cloud_control.utils.datetime_utils import format_inverter_time, parse_inverter_time

from .coordinator import SolisCloudControlCoordinator
from .entity import SolisCloudControlEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: SolisCloudControlConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    inverter = entry.runtime_data.inverter
    coordinator = entry.runtime_data.coordinator

    entities = []

    if inverter.time is not None:
        entities.append(
            InverterTimeEntity(
                coordinator=coordinator,
                entity_description=DateTimeEntityDescription(
                    key="inverter_time",
                    name="Inverter Time",
                    icon="mdi:clock-outline",
                ),
                inverter_time=inverter.time,
            )
        )

    async_add_entities(entities)


class InverterTimeEntity(SolisCloudControlEntity, DateTimeEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: DateTimeEntityDescription,
        inverter_time: InverterTime,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_time.cid)
        self.inverter_time = inverter_time

    @property
    def native_value(self) -> datetime | None:
        current_value = self.coordinator.data.get(self.inverter_time.cid)
        result = parse_inverter_time(current_value)

        if result is None:
            _LOGGER.warning("Invalid '%s' value: '%s'", self.name, current_value)

        return result

    async def async_set_value(self, value: datetime) -> None:
        value_str = format_inverter_time(value)

        _LOGGER.info("Set '%s' to %s (value: %s)", self.name, value, value_str)
        await self.coordinator.control(self.inverter_time.cid, value_str)
