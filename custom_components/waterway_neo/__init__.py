"""Waterway NEO integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WaterwayNeoClient
from .const import (
    CONF_AUTO_SYNC_CLOCK,
    CONF_CHANNEL,
    CONF_CLOCK_DRIFT_THRESHOLD,
    CONF_PUBLISH_KEY,
    CONF_SCAN_INTERVAL,
    CONF_SUBSCRIBE_KEY,
    CONF_TIME_ZONE,
    DEFAULT_AUTO_SYNC_CLOCK,
    DEFAULT_CLOCK_DRIFT_THRESHOLD,
    DEFAULT_SCAN_INTERVAL,
    PLATFORMS,
)
from .coordinator import WaterwayNeoCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Waterway NEO from a config entry."""

    client = WaterwayNeoClient(
        async_get_clientsession(hass),
        host=entry.data[CONF_HOST],
        publish_key=entry.data[CONF_PUBLISH_KEY],
        subscribe_key=entry.data[CONF_SUBSCRIBE_KEY],
        channel=entry.data[CONF_CHANNEL],
        time_zone=entry.data[CONF_TIME_ZONE],
    )
    coordinator = WaterwayNeoCoordinator(
        hass,
        entry,
        client,
        scan_interval=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        auto_sync_clock=entry.data.get(CONF_AUTO_SYNC_CLOCK, DEFAULT_AUTO_SYNC_CLOCK),
        clock_drift_threshold=entry.data.get(
            CONF_CLOCK_DRIFT_THRESHOLD, DEFAULT_CLOCK_DRIFT_THRESHOLD
        ),
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Waterway NEO config entry."""

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
