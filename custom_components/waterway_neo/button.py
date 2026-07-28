"""Button entities for Waterway NEO."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    """Set up Waterway NEO buttons."""

    coordinator: WaterwayNeoCoordinator = entry.runtime_data
    async_add_entities([WaterwayNeoSyncTimeButton(coordinator)])


class WaterwayNeoSyncTimeButton(WaterwayNeoEntity, ButtonEntity):
    """Synchronize the controller clock."""

    _attr_name = "Synchronize clock"
    _attr_icon = "mdi:clock-sync-outline"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: WaterwayNeoCoordinator) -> None:
        super().__init__(coordinator, "synchronize_clock")

    async def async_press(self) -> None:
        await self.coordinator.client.async_sync_time()
        await self.coordinator.async_request_refresh()
