"""Sensor entities for Waterway NEO."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import WaterwayNeoData
from .coordinator import WaterwayNeoCoordinator
from .entity import WaterwayNeoEntity


@dataclass(frozen=True, kw_only=True)
class WaterwayNeoSensorDescription(SensorEntityDescription):
    """Describe a Waterway NEO sensor."""

    value_fn: Callable[[WaterwayNeoData], float | int | datetime | str | None]


SENSORS = (
    WaterwayNeoSensorDescription(
        key="water_temperature",
        name="Water temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.water_temperature,
    ),
    WaterwayNeoSensorDescription(
        key="target_temperature",
        name="Target temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        value_fn=lambda data: data.target_temperature,
    ),
    WaterwayNeoSensorDescription(
        key="controller_time",
        name="Controller time",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data.controller_time,
    ),
    WaterwayNeoSensorDescription(
        key="clock_drift",
        name="Clock drift",
        native_unit_of_measurement="min",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:clock-alert-outline",
        value_fn=lambda data: data.clock_drift_minutes,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Waterway NEO sensors."""

    coordinator: WaterwayNeoCoordinator = entry.runtime_data
    async_add_entities(WaterwayNeoSensor(coordinator, description) for description in SENSORS)


class WaterwayNeoSensor(WaterwayNeoEntity, SensorEntity):
    """A Waterway NEO sensor."""

    entity_description: WaterwayNeoSensorDescription

    def __init__(
        self,
        coordinator: WaterwayNeoCoordinator,
        description: WaterwayNeoSensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | int | datetime | str | None:
        """Return the current sensor value."""

        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        """Return whether a value is available."""

        return super().available and self.native_value is not None
