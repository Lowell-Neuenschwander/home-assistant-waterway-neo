"""Constants for the Waterway NEO integration."""

from __future__ import annotations

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "waterway_neo"
NAME: Final = "Waterway NEO"

CONF_PUBLISH_KEY: Final = "publish_key"
CONF_SUBSCRIBE_KEY: Final = "subscribe_key"
CONF_CHANNEL: Final = "channel"
CONF_TIME_ZONE: Final = "time_zone"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_AUTO_SYNC_CLOCK: Final = "auto_sync_clock"
CONF_CLOCK_DRIFT_THRESHOLD: Final = "clock_drift_threshold"

DEFAULT_NAME: Final = "Waterway NEO"
DEFAULT_SCAN_INTERVAL: Final = 300
DEFAULT_AUTO_SYNC_CLOCK: Final = True
DEFAULT_CLOCK_DRIFT_THRESHOLD: Final = 5

MIN_TEMP_F: Final = 80
MAX_TEMP_F: Final = 104

PUBNUB_ORIGIN: Final = "https://ps9.pubnub.com"
PUBNUB_UUID: Final = "home-assistant-waterway-neo"

PLATFORMS: Final = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.SENSOR,
]
