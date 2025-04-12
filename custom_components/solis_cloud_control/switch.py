import logging

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry

from .const import (
    CID_CHARGE_SLOT1_SWITCH,
    CID_CHARGE_SLOT2_SWITCH,
    CID_CHARGE_SLOT3_SWITCH,
    CID_CHARGE_SLOT4_SWITCH,
    CID_CHARGE_SLOT5_SWITCH,
    CID_CHARGE_SLOT6_SWITCH,
    CID_DISCHARGE_SLOT1_SWITCH,
    CID_DISCHARGE_SLOT2_SWITCH,
    CID_DISCHARGE_SLOT3_SWITCH,
    CID_DISCHARGE_SLOT4_SWITCH,
    CID_DISCHARGE_SLOT5_SWITCH,
    CID_DISCHARGE_SLOT6_SWITCH,
)
from .coordinator import SolisCloudControlCoordinator
from .entity import SolisCloudControlEntity

_LOGGER = logging.getLogger(__name__)


_BIT_CHARGE_SLOT1 = 0
_BIT_CHARGE_SLOT2 = 1
_BIT_CHARGE_SLOT3 = 2
_BIT_CHARGE_SLOT4 = 3
_BIT_CHARGE_SLOT5 = 4
_BIT_CHARGE_SLOT6 = 5
_BIT_DISCHARGE_SLOT1 = 6
_BIT_DISCHARGE_SLOT2 = 7
_BIT_DISCHARGE_SLOT3 = 8
_BIT_DISCHARGE_SLOT4 = 9
_BIT_DISCHARGE_SLOT5 = 10
_BIT_DISCHARGE_SLOT6 = 11


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: SolisCloudControlConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
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
        old_value = self._calculate_old_value()
        _LOGGER.info("Turning on slot (old_value: %s)", old_value)
        await self.coordinator.control(self.cid, "1", old_value)

    async def async_turn_off(self, **kwargs: dict[str, any]) -> None:  # noqa: ARG002
        old_value = self._calculate_old_value()
        _LOGGER.info("Turning off slot (old_value: %s)", old_value)
        await self.coordinator.control(self.cid, "0", old_value)

    def _calculate_old_value(self) -> str:
        if not self.coordinator.data:
            return "0"

        slot_states = {
            _BIT_CHARGE_SLOT1: self.coordinator.data.get(CID_CHARGE_SLOT1_SWITCH) == "1",
            _BIT_CHARGE_SLOT2: self.coordinator.data.get(CID_CHARGE_SLOT2_SWITCH) == "1",
            _BIT_CHARGE_SLOT3: self.coordinator.data.get(CID_CHARGE_SLOT3_SWITCH) == "1",
            _BIT_CHARGE_SLOT4: self.coordinator.data.get(CID_CHARGE_SLOT4_SWITCH) == "1",
            _BIT_CHARGE_SLOT5: self.coordinator.data.get(CID_CHARGE_SLOT5_SWITCH) == "1",
            _BIT_CHARGE_SLOT6: self.coordinator.data.get(CID_CHARGE_SLOT6_SWITCH) == "1",
            _BIT_DISCHARGE_SLOT1: self.coordinator.data.get(CID_DISCHARGE_SLOT1_SWITCH) == "1",
            _BIT_DISCHARGE_SLOT2: self.coordinator.data.get(CID_DISCHARGE_SLOT2_SWITCH) == "1",
            _BIT_DISCHARGE_SLOT3: self.coordinator.data.get(CID_DISCHARGE_SLOT3_SWITCH) == "1",
            _BIT_DISCHARGE_SLOT4: self.coordinator.data.get(CID_DISCHARGE_SLOT4_SWITCH) == "1",
            _BIT_DISCHARGE_SLOT5: self.coordinator.data.get(CID_DISCHARGE_SLOT5_SWITCH) == "1",
            _BIT_DISCHARGE_SLOT6: self.coordinator.data.get(CID_DISCHARGE_SLOT6_SWITCH) == "1",
        }

        value = 0
        for bit_position, is_enabled in slot_states.items():
            if is_enabled:
                value |= 1 << bit_position

        return str(value)
