from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CID_CHARGE_SLOT1_SWITCH, CID_DISCHARGE_SLOT1_SWITCH
from .coordinator import SolisCloudControlCoordinator
from .entity import SolisCloudControlEntity


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SolisCloudControlCoordinator = entry.runtime_data
    async_add_entities(
        [
            SlotSwitch(
                coordinator=coordinator,
                entity_description=SwitchEntityDescription(
                    key="slot1_charge_switch",
                    name="Slot1 Charge",
                    icon="mdi:battery-plus-outline",
                ),
                cid=CID_CHARGE_SLOT1_SWITCH,
            ),
            SlotSwitch(
                coordinator=coordinator,
                entity_description=SwitchEntityDescription(
                    key="slot1_discharge_switch",
                    name="Slot1 Discharge",
                    icon="mdi:battery-minus-outline",
                ),
                cid=CID_DISCHARGE_SLOT1_SWITCH,
            ),
        ]
    )


class SlotSwitch(SolisCloudControlEntity, SwitchEntity):
    def __init__(
        self, coordinator: SolisCloudControlCoordinator, entity_description: SwitchEntityDescription, cid: int
    ) -> None:
        super().__init__(coordinator, entity_description, cid)

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None

        value = self.coordinator.data.get(self.cid)
        return value == "1" if value is not None else None

    async def async_turn_on(self, **kwargs: dict[str, any]) -> None:  # noqa: ARG002
        await self.coordinator.api_client.control(self.coordinator.inverter_sn, self.cid, "1", "0")
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: dict[str, any]) -> None:  # noqa: ARG002
        await self.coordinator.api_client.control(self.coordinator.inverter_sn, self.cid, "0", "1")
        await self.coordinator.async_request_refresh()
