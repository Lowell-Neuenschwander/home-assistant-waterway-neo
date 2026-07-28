"""Binary sensors for Waterway NEO."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import WaterwayNeoCoordinator
from .entity import WaterwayNeoEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Waterway NEO binary sensors."""

    coordinator: WaterwayNeoCoordinator = entry.runtime_data
    async_add_entities(
        [
            WaterwayNeoOnlineBinarySensor(coordinator),
            WaterwayNeoCloudBinarySensor(coordinator),
            WaterwayNeoClockBinarySensor(coordinator),
        ]
    )


class WaterwayNeoOnlineBinarySensor(WaterwayNeoEntity, BinarySensorEntity):
    """Controller LAN connectivity."""

    _attr_name = "Controller connection"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: WaterwayNeoCoordinator) -> None:
        super().__init__(coordinator, "controller_connection")

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.online


class WaterwayNeoCloudBinarySensor(WaterwayNeoEntity, BinarySensorEntity):
    """Controller cloud-channel connectivity."""

    _attr_name = "Cloud connection"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: WaterwayNeoCoordinator) -> None:
        super().__init__(coordinator, "cloud_connection")

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.cloud_available


class WaterwayNeoClockBinarySensor(WaterwayNeoEntity, BinarySensorEntity):
    """Whether the controller clock is within configured tolerance."""

    _attr_name = "Clock synchronized"
    _attr_icon = "mdi:clock-check-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: WaterwayNeoCoordinator) -> None:
        super().__init__(coordinator, "clock_synchronized")

    @property
    def is_on(self) -> bool | None:
        drift = self.coordinator.data.clock_drift_minutes
        if drift is None:
            return None
        return abs(drift) <= self.coordinator.clock_drift_threshold

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.clock_drift_minutes is not None
