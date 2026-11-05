import logging

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry
from custom_components.solis_cloud_control.domain.storage_mode import StorageMode
from custom_components.solis_cloud_control.inverters.inverter import (
    InverterAllowExport,
    InverterChargeDischargeSlot,
    InverterChargeDischargeSlots,
    InverterMpptScanning,
    InverterOnOff,
    InverterStorageMode,
)

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

    if inverter.on_off is not None:
        entities.append(
            OnOffSwitch(
                coordinator=coordinator,
                entity_description=SwitchEntityDescription(
                    key="on_off_switch",
                    name="Inverter On/Off",
                    icon="mdi:power",
                ),
                inverter_on_off=inverter.on_off,
            )
        )

    if inverter.allow_export is not None and inverter.storage_mode is not None:
        entities.append(
            AllowExportSwitch(
                coordinator=coordinator,
                entity_description=SwitchEntityDescription(
                    key="allow_export_switch",
                    name="Allow Export",
                    icon="mdi:transmission-tower-export",
                ),
                inverter_allow_export=inverter.allow_export,
                inverter_storage_mode=inverter.storage_mode,
            )
        )

    charge_discharge_slots = inverter.charge_discharge_slots

    if charge_discharge_slots is not None:
        for i in range(1, charge_discharge_slots.SLOTS_COUNT + 1):
            entities.append(
                SlotV2Switch(
                    coordinator=coordinator,
                    entity_description=SwitchEntityDescription(
                        key=f"slot{i}_charge_switch",
                        name=f"Slot{i} Charge",
                        icon="mdi:battery-plus-outline",
                    ),
                    inverter_charge_discharge_slot=charge_discharge_slots.get_charge_slot(i),
                    inverter_charge_discharge_slots=charge_discharge_slots,
                )
            )
            entities.append(
                SlotV2Switch(
                    coordinator=coordinator,
                    entity_description=SwitchEntityDescription(
                        key=f"slot{i}_discharge_switch",
                        name=f"Slot{i} Discharge",
                        icon="mdi:battery-minus-outline",
                    ),
                    inverter_charge_discharge_slot=charge_discharge_slots.get_discharge_slot(i),
                    inverter_charge_discharge_slots=charge_discharge_slots,
                )
            )

    if inverter.storage_mode is not None:
        entities.append(
            BatteryReserveSwitch(
                coordinator=coordinator,
                entity_description=SwitchEntityDescription(
                    key="battery_reserve",
                    name="Battery Reserve",
                    icon="mdi:battery-heart-outline",
                ),
                inverter_storage_mode=inverter.storage_mode,
            )
        )
        entities.append(
            AllowGridChargingSwitch(
                coordinator=coordinator,
                entity_description=SwitchEntityDescription(
                    key="allow_grid_charging",
                    name="Allow Grid Charging",
                    icon="mdi:battery-charging-outline",
                ),
                inverter_storage_mode=inverter.storage_mode,
            )
        )
        entities.append(
            GridPeakShavingSwitch(
                coordinator=coordinator,
                entity_description=SwitchEntityDescription(
                    key="grid_peak_shaving",
                    name="Grid Peak Shaving",
                    icon="mdi:chart-bell-curve",
                ),
                inverter_storage_mode=inverter.storage_mode,
            )
        )

    if inverter.storage_mode is not None and not inverter.info.is_tou_v2_enabled:
        entities.append(
            TimeOfUseSwitch(
                coordinator=coordinator,
                entity_description=SwitchEntityDescription(
                    key="time_of_use_switch",
                    name="Time of Use",
                    icon="mdi:clock-check-outline",
                ),
                inverter_storage_mode=inverter.storage_mode,
            )
        )

    if inverter.mppt_scanning is not None:
        entities.append(
            MpptScanningSwitch(
                coordinator=coordinator,
                entity_description=SwitchEntityDescription(
                    key="mppt_scanning_switch",
                    name="MPPT Multi-peak Scanning",
                    icon="mdi:solar-power-variant",
                ),
                inverter_mppt_scanning=inverter.mppt_scanning,
            )
        )

    async_add_entities(entities)


class OnOffSwitch(SolisCloudControlEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: SwitchEntityDescription,
        inverter_on_off: InverterOnOff,
    ) -> None:
        super().__init__(coordinator, entity_description, [inverter_on_off.on_cid, inverter_on_off.off_cid])
        self.inverter_on_off = inverter_on_off

        self._update_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_state()
        super()._handle_coordinator_update()

    async def async_turn_on(self, **kwargs) -> None:  # noqa: ANN003, ARG002
        _LOGGER.info("Turn on '%s'", self.name)
        await self.coordinator.control(self.inverter_on_off.on_cid, self.inverter_on_off.on_value)

    async def async_turn_off(self, **kwargs) -> None:  # noqa: ANN003, ARG002
        _LOGGER.info("Turn off '%s'", self.name)
        await self.coordinator.control(self.inverter_on_off.off_cid, self.inverter_on_off.off_value)

    def _update_state(self) -> None:
        on_value = self.coordinator.data.get(self.inverter_on_off.on_cid)
        off_value = self.coordinator.data.get(self.inverter_on_off.off_cid)

        same_values = on_value == off_value
        valid_values = self.inverter_on_off.is_valid_value(on_value) and self.inverter_on_off.is_valid_value(off_value)

        self._attr_assumed_state = not (same_values and valid_values)
        self._attr_is_on = on_value == self.inverter_on_off.on_value if same_values and valid_values else None


class AllowExportSwitch(SolisCloudControlEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: SwitchEntityDescription,
        inverter_allow_export: InverterAllowExport,
        inverter_storage_mode: InverterStorageMode,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_allow_export.cid)
        self.inverter_allow_export = inverter_allow_export
        self.inverter_storage_mode = inverter_storage_mode

        self._update_is_on()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_is_on()
        super()._handle_coordinator_update()

    @property
    def available(self) -> bool:
        if not super().available:
            return False

        storage_mode_value = self.coordinator.data.get(self.inverter_storage_mode.cid)
        storage_mode = StorageMode.create(storage_mode_value)
        if storage_mode is None:
            _LOGGER.warning("Invalid '%s' storage mode: '%s'", self.name, storage_mode_value)
            return False

        return storage_mode.is_self_use()

    async def async_turn_on(self, **kwargs) -> None:  # noqa: ANN003, ARG002
        old_value = self._calculate_old_value()
        _LOGGER.info("Turn on '%s' (old_value: %s)", self.name, old_value)
        await self.coordinator.control(self.inverter_allow_export.cid, "0", old_value)

    async def async_turn_off(self, **kwargs) -> None:  # noqa: ANN003, ARG002
        old_value = self._calculate_old_value()
        _LOGGER.info("Turn off '%s' (old_value: %s)", self.name, old_value)
        await self.coordinator.control(self.inverter_allow_export.cid, "1", old_value)

    def _calculate_old_value(self) -> str:
        if self.is_on:
            return self.inverter_allow_export.on_value
        else:
            return self.inverter_allow_export.off_value

    def _update_is_on(self) -> None:
        value = self.coordinator.data.get(self.inverter_allow_export.cid)
        self._attr_is_on = value == "0" if value is not None else None


class SlotV2Switch(SolisCloudControlEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: SwitchEntityDescription,
        inverter_charge_discharge_slot: InverterChargeDischargeSlot,
        inverter_charge_discharge_slots: InverterChargeDischargeSlots,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_charge_discharge_slots.all_cids)

        self.inverter_charge_discharge_slot = inverter_charge_discharge_slot
        self.inverter_charge_discharge_slots = inverter_charge_discharge_slots

        self._update_is_on()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_is_on()
        super()._handle_coordinator_update()

    async def async_turn_on(self, **kwargs) -> None:  # noqa: ANN003, ARG002
        old_value = self._calculate_old_value()
        _LOGGER.info("Turn on '%s' (old_value: %s)", self.name, old_value)
        await self.coordinator.control(self.inverter_charge_discharge_slot.switch_cid, "1", old_value)

    async def async_turn_off(self, **kwargs) -> None:  # noqa: ANN003, ARG002
        old_value = self._calculate_old_value()
        _LOGGER.info("Turn off '%s' (old_value: %s)", self.name, old_value)
        await self.coordinator.control(self.inverter_charge_discharge_slot.switch_cid, "0", old_value)

    def _calculate_old_value(self) -> str:
        slots = self.inverter_charge_discharge_slots
        data = self.coordinator.data

        slot_states = {
            slots.bit_charge_slot1: data.get(slots.charge_slot1.switch_cid) == "1",
            slots.bit_charge_slot2: data.get(slots.charge_slot2.switch_cid) == "1",
            slots.bit_charge_slot3: data.get(slots.charge_slot3.switch_cid) == "1",
            slots.bit_charge_slot4: data.get(slots.charge_slot4.switch_cid) == "1",
            slots.bit_charge_slot5: data.get(slots.charge_slot5.switch_cid) == "1",
            slots.bit_charge_slot6: data.get(slots.charge_slot6.switch_cid) == "1",
            slots.bit_discharge_slot1: data.get(slots.discharge_slot1.switch_cid) == "1",
            slots.bit_discharge_slot2: data.get(slots.discharge_slot2.switch_cid) == "1",
            slots.bit_discharge_slot3: data.get(slots.discharge_slot3.switch_cid) == "1",
            slots.bit_discharge_slot4: data.get(slots.discharge_slot4.switch_cid) == "1",
            slots.bit_discharge_slot5: data.get(slots.discharge_slot5.switch_cid) == "1",
            slots.bit_discharge_slot6: data.get(slots.discharge_slot6.switch_cid) == "1",
        }

        value = 0
        for bit_position, is_enabled in slot_states.items():
            if is_enabled:
                value |= 1 << bit_position

        return str(value)

    def _update_is_on(self) -> None:
        value = self.coordinator.data.get(self.inverter_charge_discharge_slot.switch_cid)
        self._attr_is_on = value == "1" if value is not None else None


class BatteryReserveSwitch(SolisCloudControlEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: SwitchEntityDescription,
        inverter_storage_mode: InverterStorageMode,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_storage_mode.cid)
        self.inverter_storage_mode = inverter_storage_mode

        self._update_is_on()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_is_on()
        super()._handle_coordinator_update()

    async def async_turn_on(self, **kwargs) -> None:  # noqa: ANN003, ARG002
        current_value = self.coordinator.data.get(self.inverter_storage_mode.cid)

        storage_mode = StorageMode.create(current_value)
        if storage_mode is None:
            _LOGGER.warning("Invalid '%s' storage mode: '%s'", self.name, current_value)
            return None

        storage_mode.enable_battery_reserve()

        value_str = storage_mode.to_value()

        _LOGGER.info("Turn on '%s' (value: %s)", self.name, value_str)
        await self.coordinator.control(self.inverter_storage_mode.cid, value_str)

    async def async_turn_off(self, **kwargs) -> None:  # noqa: ANN003, ARG002
        current_value = self.coordinator.data.get(self.inverter_storage_mode.cid)

        storage_mode = StorageMode.create(current_value)
        if storage_mode is None:
            _LOGGER.warning("Invalid '%s' storage mode: '%s'", self.name, current_value)
            return None

        storage_mode.disable_battery_reserve()

        value_str = storage_mode.to_value()

        _LOGGER.info("Turn off '%s' (value: %s)", self.name, value_str)
        await self.coordinator.control(self.inverter_storage_mode.cid, value_str)

    def _update_is_on(self) -> None:
        current_value = self.coordinator.data.get(self.inverter_storage_mode.cid)

        storage_mode = StorageMode.create(current_value)
        if storage_mode is None:
            _LOGGER.warning("Invalid '%s' storage mode: '%s'", self.name, current_value)
            self._attr_is_on = None
        else:
            self._attr_is_on = storage_mode.is_battery_reserve_enabled()


class AllowGridChargingSwitch(SolisCloudControlEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: SwitchEntityDescription,
        inverter_storage_mode: InverterStorageMode,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_storage_mode.cid)
        self.inverter_storage_mode = inverter_storage_mode

        self._update_is_on()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_is_on()
        super()._handle_coordinator_update()

    async def async_turn_on(self, **kwargs) -> None:  # noqa: ANN003, ARG002
        current_value = self.coordinator.data.get(self.inverter_storage_mode.cid)

        storage_mode = StorageMode.create(current_value)
        if storage_mode is None:
            _LOGGER.warning("Invalid '%s' storage mode: '%s'", self.name, current_value)
            return None

        storage_mode.enable_allow_grid_charging()

        value_str = storage_mode.to_value()

        _LOGGER.info("Turn on '%s' (value: %s)", self.name, value_str)
        await self.coordinator.control(self.inverter_storage_mode.cid, value_str)

    async def async_turn_off(self, **kwargs) -> None:  # noqa: ANN003, ARG002
        current_value = self.coordinator.data.get(self.inverter_storage_mode.cid)

        storage_mode = StorageMode.create(current_value)
        if storage_mode is None:
            _LOGGER.warning("Invalid '%s' storage mode: '%s'", self.name, current_value)
            return None

        storage_mode.disable_allow_grid_charging()

        value_str = storage_mode.to_value()

        _LOGGER.info("Turn off '%s' (value: %s)", self.name, value_str)
        await self.coordinator.control(self.inverter_storage_mode.cid, value_str)

    def _update_is_on(self) -> None:
        current_value = self.coordinator.data.get(self.inverter_storage_mode.cid)

        storage_mode = StorageMode.create(current_value)
        if storage_mode is None:
            _LOGGER.warning("Invalid '%s' storage mode: '%s'", self.name, current_value)
            self._attr_is_on = None
        else:
            self._attr_is_on = storage_mode.is_allow_grid_charging()


class GridPeakShavingSwitch(SolisCloudControlEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: SwitchEntityDescription,
        inverter_storage_mode: InverterStorageMode,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_storage_mode.cid)
        self.inverter_storage_mode = inverter_storage_mode

        self._update_is_on()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_is_on()
        super()._handle_coordinator_update()

    @property
    def available(self) -> bool:
        if not super().available:
            return False

        storage_mode_value = self.coordinator.data.get(self.inverter_storage_mode.cid)
        storage_mode = StorageMode.create(storage_mode_value)
        if storage_mode is None:
            _LOGGER.warning("Invalid '%s' storage mode: '%s'", self.name, storage_mode_value)
            return False

        return storage_mode.is_self_use() or storage_mode.is_feed_in_priority()

    async def async_turn_on(self, **kwargs) -> None:  # noqa: ANN003, ARG002
        current_value = self.coordinator.data.get(self.inverter_storage_mode.cid)

        storage_mode = StorageMode.create(current_value)
        assert storage_mode is not None  # `available` rejects invalid storage modes

        storage_mode.enable_peak_shaving()

        value_str = storage_mode.to_value()

        _LOGGER.info("Turn on '%s' (value: %s)", self.name, value_str)
        await self.coordinator.control(self.inverter_storage_mode.cid, value_str)

    async def async_turn_off(self, **kwargs) -> None:  # noqa: ANN003, ARG002
        current_value = self.coordinator.data.get(self.inverter_storage_mode.cid)

        storage_mode = StorageMode.create(current_value)
        assert storage_mode is not None  # `available` rejects invalid storage modes

        storage_mode.disable_peak_shaving()

        value_str = storage_mode.to_value()

        _LOGGER.info("Turn off '%s' (value: %s)", self.name, value_str)
        await self.coordinator.control(self.inverter_storage_mode.cid, value_str)

    def _update_is_on(self) -> None:
        current_value = self.coordinator.data.get(self.inverter_storage_mode.cid)

        # runs also when unavailable, `available` already warns about invalid storage modes
        storage_mode = StorageMode.create(current_value)
        self._attr_is_on = storage_mode.is_peak_shaving() if storage_mode is not None else None


class TimeOfUseSwitch(SolisCloudControlEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: SwitchEntityDescription,
        inverter_storage_mode: InverterStorageMode,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_storage_mode.cid)
        self.inverter_storage_mode = inverter_storage_mode

        self._update_is_on()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_is_on()
        super()._handle_coordinator_update()

    async def async_turn_on(self, **kwargs) -> None:  # noqa: ANN003, ARG002
        current_value = self.coordinator.data.get(self.inverter_storage_mode.cid)

        storage_mode = StorageMode.create(current_value)
        if storage_mode is None:
            _LOGGER.warning("Invalid '%s' storage mode: '%s'", self.name, current_value)
            return None

        storage_mode.enable_tou_mode()

        value_str = storage_mode.to_value()

        _LOGGER.info("Turn on '%s' (value: %s)", self.name, value_str)
        await self.coordinator.control(self.inverter_storage_mode.cid, value_str)

    async def async_turn_off(self, **kwargs) -> None:  # noqa: ANN003, ARG002
        current_value = self.coordinator.data.get(self.inverter_storage_mode.cid)

        storage_mode = StorageMode.create(current_value)
        if storage_mode is None:
            _LOGGER.warning("Invalid '%s' storage mode: '%s'", self.name, current_value)
            return None

        storage_mode.disable_tou_mode()

        value_str = storage_mode.to_value()

        _LOGGER.info("Turn off '%s' (value: %s)", self.name, value_str)
        await self.coordinator.control(self.inverter_storage_mode.cid, value_str)

    def _update_is_on(self) -> None:
        current_value = self.coordinator.data.get(self.inverter_storage_mode.cid)

        storage_mode = StorageMode.create(current_value)
        if storage_mode is None:
            _LOGGER.warning("Invalid '%s' storage mode: '%s'", self.name, current_value)
            self._attr_is_on = None
        else:
            self._attr_is_on = storage_mode.is_tou_mode()


class MpptScanningSwitch(SolisCloudControlEntity, SwitchEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: SwitchEntityDescription,
        inverter_mppt_scanning: InverterMpptScanning,
    ) -> None:
        super().__init__(coordinator, entity_description, inverter_mppt_scanning.cid)
        self.inverter_mppt_scanning = inverter_mppt_scanning

        self._update_is_on()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_is_on()
        super()._handle_coordinator_update()

    async def async_turn_on(self, **kwargs) -> None:  # noqa: ANN003, ARG002
        old_value = self._calculate_old_value()
        _LOGGER.info("Turn on '%s' (old_value: %s)", self.name, old_value)
        await self.coordinator.control(self.inverter_mppt_scanning.cid, "1", old_value)

    async def async_turn_off(self, **kwargs) -> None:  # noqa: ANN003, ARG002
        old_value = self._calculate_old_value()
        _LOGGER.info("Turn off '%s' (old_value: %s)", self.name, old_value)
        await self.coordinator.control(self.inverter_mppt_scanning.cid, "0", old_value)

    def _calculate_old_value(self) -> str:
        if self.is_on:
            return self.inverter_mppt_scanning.on_value
        else:
            return self.inverter_mppt_scanning.off_value

    def _update_is_on(self) -> None:
        value = self.coordinator.data.get(self.inverter_mppt_scanning.cid)
        self._attr_is_on = value == self.inverter_mppt_scanning.on_value if value is not None else None
