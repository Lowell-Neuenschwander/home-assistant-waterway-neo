"""Shared entity base for Waterway NEO."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WaterwayNeoCoordinator


class WaterwayNeoEntity(CoordinatorEntity[WaterwayNeoCoordinator]):
    """Base class for Waterway NEO entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: WaterwayNeoCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            manufacturer="Waterway Plastics",
            model="NEO Wi-Fi Controller",
            name=coordinator.entry.title,
            configuration_url=f"http://{coordinator.client.host}/",
        )
