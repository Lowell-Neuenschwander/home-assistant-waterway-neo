"""Data coordinator for Waterway NEO."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import WaterwayNeoClient, WaterwayNeoData, WaterwayNeoError
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
        self.local_consecutive_failures = 0
        self.cloud_consecutive_failures = 0
        self.last_local_success: datetime | None = None
        self.last_cloud_success: datetime | None = None

    async def _async_update_data(self) -> WaterwayNeoData:
        data = await self.client.async_get_data()
        now = datetime.now(UTC)
        self.local_consecutive_failures = self._record_channel_result(
            channel="local",
            available=data.local_available and data.online,
            error=data.local_error,
            failures=self.local_consecutive_failures,
        )
        if data.local_available and data.online:
            self.last_local_success = now
        self.cloud_consecutive_failures = self._record_channel_result(
            channel="cloud",
            available=data.cloud_available,
            error=data.cloud_error,
            failures=self.cloud_consecutive_failures,
        )
        if data.cloud_available:
            self.last_cloud_success = now

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

    @staticmethod
    def _record_channel_result(
        *, channel: str, available: bool, error: str | None, failures: int
    ) -> int:
        """Track and log channel failures without flooding the log."""

        if available:
            if failures:
                _LOGGER.info("Waterway NEO %s communication recovered", channel)
            return 0
        if failures == 0:
            _LOGGER.warning(
                "Waterway NEO %s communication failed: %s",
                channel,
                error or "unknown error",
            )
        return failures + 1
