"""Pure protocol helpers for Waterway NEO controllers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

MIN_TEMP_F = 80
MAX_TEMP_F = 104


@dataclass(frozen=True)
class LocalStatus:
    """Parsed controller-local state."""

    online: bool
    water_temperature: int | None
    raw_status: str
    other_status: str


def _hex_temperature(candidate: str) -> int | None:
    if len(candidate) != 2:
        return None
    try:
        value = int(candidate, 16)
    except ValueError:
        return None
    return value if MIN_TEMP_F <= value <= MAX_TEMP_F else None


def parse_local_status(xml_text: str) -> LocalStatus:
    """Parse the controller's local status.xml response."""

    root = ElementTree.fromstring(xml_text)
    raw_status = (root.findtext("ctrlstatus") or "").strip()
    other_status = (root.findtext("ctrlother") or "").strip()
    fields = raw_status.split(",")
    water_temperature = _hex_temperature(fields[6]) if len(fields) > 6 else None
    online = raw_status.startswith("$G0,") and raw_status.endswith("AA,55")
    return LocalStatus(online, water_temperature, raw_status, other_status)


def _other_message(message: Mapping[str, Any] | Any) -> str:
    if not isinstance(message, Mapping):
        return ""
    return str(message.get("OtherMsg", "")).strip()


def parse_target_message(message: Mapping[str, Any] | Any) -> tuple[int | None, str]:
    """Parse a G7/A7 target-temperature response."""

    raw = _other_message(message)
    fields = raw.split(",")
    if len(fields) < 3 or fields[0] not in ("$G7", "$A7"):
        return None, raw
    candidate = fields[-4] if fields[0] == "$A7" and len(fields) >= 6 else fields[2]
    return _hex_temperature(candidate), raw


def parse_clock_message(
    message: Mapping[str, Any] | Any, time_zone: ZoneInfo
) -> tuple[datetime | None, str]:
    """Parse a G2/A2 controller date/time response."""

    raw = _other_message(message)
    fields = raw.split(",")
    if len(fields) < 12 or fields[0] not in ("$G2", "$A2"):
        return None, raw
    try:
        value = datetime(
            2000 + int(fields[2], 10),
            int(fields[3], 10),
            int(fields[4], 10),
            int(fields[6], 10),
            int(fields[7], 10),
            int(fields[8], 10),
            tzinfo=time_zone,
        )
    except (TypeError, ValueError):
        return None, raw
    return value, raw


def build_set_temperature_command(temperature: int) -> str:
    """Build a validated S3 target-temperature command."""

    if not MIN_TEMP_F <= temperature <= MAX_TEMP_F:
        raise ValueError(f"temperature must be {MIN_TEMP_F}-{MAX_TEMP_F} F")
    return f"$S3,0,{temperature:02X},!,AA,55"


def build_set_time_command(value: datetime) -> str:
    """Build the S6 command used by the Waterway app.

    The controller uses Sunday=0 through Saturday=6 for the weekday field.
    Seconds are intentionally reset to zero, matching the official app.
    """

    weekday = int(value.strftime("%w"))
    return (
        f"$S6,1,D,{value.year % 100:02d},{value.month:02d},{value.day:02d},"
        f"W,{weekday},T,{value.hour:02d},{value.minute:02d},00,!,AA,55"
    )
