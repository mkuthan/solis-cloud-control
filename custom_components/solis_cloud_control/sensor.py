from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.solis_cloud_control.data import SolisCloudControlConfigEntry
from custom_components.solis_cloud_control.inverters.inverter import (
    InverterBatteryForceChargeSOC,
    InverterBatteryMaxChargeSOC,
    InverterBatteryOverDischargeSOC,
    InverterBatteryRecoverySOC,
    InverterBatteryReserveSOC,
)
from custom_components.solis_cloud_control.safe_converters import safe_get_float_value

from .coordinator import SolisCloudControlCoordinator
from .entity import SolisCloudControlEntity


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: SolisCloudControlConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    inverter = entry.runtime_data.inverter
    coordinator = entry.runtime_data.coordinator

    entities = []

    if inverter.battery_force_charge_soc is not None:
        entities.append(
            BatterySocSensor(
                coordinator=coordinator,
                entity_description=SensorEntityDescription(
                    key="battery_force_charge_soc",
                    name="Battery Force Charge SOC",
                    icon="mdi:battery-alert-variant-outline",
                ),
                battery_soc=inverter.battery_force_charge_soc,
            )
        )
    if inverter.battery_over_discharge_soc is not None:
        entities.append(
            BatterySocSensor(
                coordinator=coordinator,
                entity_description=SensorEntityDescription(
                    key="battery_over_discharge_soc",
                    name="Battery Over Discharge SOC",
                    icon="mdi:battery-50",
                ),
                battery_soc=inverter.battery_over_discharge_soc,
            )
        )
    if inverter.battery_recovery_soc is not None:
        entities.append(
            BatterySocSensor(
                coordinator=coordinator,
                entity_description=SensorEntityDescription(
                    key="battery_recovery_soc",
                    name="Battery Recovery SOC",
                    icon="mdi:battery-50",
                ),
                battery_soc=inverter.battery_recovery_soc,
            )
        )
    if inverter.battery_reserve_soc is not None:
        entities.append(
            BatterySocSensor(
                coordinator=coordinator,
                entity_description=SensorEntityDescription(
                    key="battery_reserve_soc",
                    name="Battery Reserve SOC",
                    icon="mdi:battery-50",
                ),
                battery_soc=inverter.battery_reserve_soc,
            )
        )
    if inverter.battery_max_charge_soc is not None:
        entities.append(
            BatterySocSensor(
                coordinator=coordinator,
                entity_description=SensorEntityDescription(
                    key="battery_max_charge_soc",
                    name="Battery Max Charge SOC",
                    icon="mdi:battery",
                ),
                battery_soc=inverter.battery_max_charge_soc,
            )
        )

    async_add_entities(entities)


class BatterySocSensor(SolisCloudControlEntity, SensorEntity):
    def __init__(
        self,
        coordinator: SolisCloudControlCoordinator,
        entity_description: SensorEntityDescription,
        battery_soc: InverterBatteryReserveSOC
        | InverterBatteryOverDischargeSOC
        | InverterBatteryForceChargeSOC
        | InverterBatteryRecoverySOC
        | InverterBatteryMaxChargeSOC,
    ) -> None:
        super().__init__(coordinator, entity_description)
        self._attr_native_unit_of_measurement = PERCENTAGE

        self.battery_soc = battery_soc

    @property
    def native_value(self) -> float | None:
        value_str = self.coordinator.data.get(self.battery_soc.cid)
        return safe_get_float_value(value_str)
