"""Diagnostics support for Waterway NEO."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_CHANNEL, CONF_PUBLISH_KEY, CONF_SUBSCRIBE_KEY
from .coordinator import WaterwayNeoCoordinator

TO_REDACT = {CONF_CHANNEL, CONF_PUBLISH_KEY, CONF_SUBSCRIBE_KEY}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return redacted diagnostics for a config entry."""

    coordinator: WaterwayNeoCoordinator = entry.runtime_data
    return {
        "config_entry": async_redact_data(dict(entry.data), TO_REDACT),
        "data": asdict(coordinator.data),
        "last_update_success": coordinator.last_update_success,
    }
