"""Data coordinator for Waterway NEO."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WaterwayNeoClient, WaterwayNeoConnectionError, WaterwayNeoData, WaterwayNeoError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class WaterwayNeoCoordinator(DataUpdateCoordinator[WaterwayNeoData]):
    """Coordinate controller polling and clock protection."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: WaterwayNeoClient,
        *,
        scan_interval: int,
        auto_sync_clock: bool,
        clock_drift_threshold: int,
        high_temperature_threshold: int,
        freeze_risk_threshold: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=scan_interval),
            config_entry=entry,
            always_update=False,
        )
        self.entry = entry
        self.client = client
        self.auto_sync_clock = auto_sync_clock
        self.clock_drift_threshold = clock_drift_threshold
        self.high_temperature_threshold = high_temperature_threshold
        self.freeze_risk_threshold = freeze_risk_threshold

    async def _async_update_data(self) -> WaterwayNeoData:
        try:
            data = await self.client.async_get_data()
        except WaterwayNeoConnectionError as err:
            raise UpdateFailed("Unable to reach the Waterway NEO controller") from err

        if (
            self.auto_sync_clock
            and data.clock_drift_minutes is not None
            and abs(data.clock_drift_minutes) > self.clock_drift_threshold
        ):
            try:
                await self.client.async_sync_time()
                data = await self.client.async_get_data()
            except WaterwayNeoError as err:
                _LOGGER.warning("Automatic Waterway NEO clock synchronization failed: %s", err)
        return data
