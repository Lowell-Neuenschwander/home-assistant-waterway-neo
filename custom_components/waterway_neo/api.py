"""Async client for Waterway NEO local and cloud APIs."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import quote
from zoneinfo import ZoneInfo

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import PUBNUB_ORIGIN, PUBNUB_UUID
from .protocol import (
    LocalStatus,
    build_set_temperature_command,
    build_set_time_command,
    parse_clock_message,
    parse_local_status,
    parse_target_message,
)


class WaterwayNeoError(Exception):
    """Base Waterway NEO error."""


class WaterwayNeoConnectionError(WaterwayNeoError):
    """Raised when the controller cannot be reached."""


class WaterwayNeoCloudError(WaterwayNeoError):
    """Raised when the PubNub channel cannot be used."""


@dataclass(frozen=True)
class WaterwayNeoData:
    """Combined local and cloud state."""

    online: bool
    water_temperature: int | None
    target_temperature: int | None
    controller_time: datetime | None
    clock_drift_minutes: float | None
    cloud_available: bool
    raw_status: str
    other_status: str


class WaterwayNeoClient:
    """Client for a single Waterway NEO controller."""

    def __init__(
        self,
        session: ClientSession,
        *,
        host: str,
        publish_key: str,
        subscribe_key: str,
        channel: str,
        time_zone: str,
    ) -> None:
        self._session = session
        self._host = host.strip().removeprefix("http://").removeprefix("https://").rstrip("/")
        self._publish_key = publish_key.strip()
        self._subscribe_key = subscribe_key.strip()
        self._channel = channel.strip()
        self._time_zone = ZoneInfo(time_zone)

    @property
    def host(self) -> str:
        """Return the configured host."""

        return self._host

    async def async_get_local_status(self) -> LocalStatus:
        """Read status.xml from the controller's LAN address."""

        try:
            async with self._session.get(
                f"http://{self._host}/status.xml",
                timeout=ClientTimeout(total=8),
            ) as response:
                response.raise_for_status()
                return parse_local_status(await response.text())
        except (ClientError, TimeoutError, ValueError) as err:
            raise WaterwayNeoConnectionError("Unable to read local controller status") from err

    async def _async_subscribe(
        self, timetoken: str, *, timeout: int = 6
    ) -> tuple[list[dict[str, Any]], str]:
        channel = quote(self._channel, safe="")
        subscribe_key = quote(self._subscribe_key, safe="")
        url = f"{PUBNUB_ORIGIN}/subscribe/{subscribe_key}/{channel}/0/{timetoken}"
        try:
            async with self._session.get(
                url,
                params={"uuid": PUBNUB_UUID},
                timeout=ClientTimeout(total=timeout),
            ) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError, json.JSONDecodeError) as err:
            raise WaterwayNeoCloudError("Unable to subscribe to controller channel") from err
        if not isinstance(payload, list) or len(payload) < 2:
            raise WaterwayNeoCloudError("Unexpected subscribe response")
        messages = [item for item in payload[0] if isinstance(item, dict)]
        return messages, str(payload[1])

    async def _async_publish(self, command: str) -> None:
        message = quote(json.dumps({"cmd": command}, separators=(",", ":")), safe="")
        publish_key = quote(self._publish_key, safe="")
        subscribe_key = quote(self._subscribe_key, safe="")
        channel = quote(self._channel, safe="")
        url = f"{PUBNUB_ORIGIN}/publish/{publish_key}/{subscribe_key}/0/{channel}/0/{message}"
        try:
            async with self._session.get(
                url,
                params={"uuid": PUBNUB_UUID},
                timeout=ClientTimeout(total=8),
            ) as response:
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError, json.JSONDecodeError) as err:
            raise WaterwayNeoCloudError("Unable to publish controller command") from err
        if not isinstance(payload, list) or not payload or payload[0] != 1:
            raise WaterwayNeoCloudError("Controller command was rejected")

    async def async_read_cloud_state(
        self,
    ) -> tuple[int | None, datetime | None]:
        """Read target temperature and controller time from PubNub."""

        _, token = await self._async_subscribe("0")
        await self._async_publish("$G7,0,!,AA,55")
        await self._async_publish("$G2,0,!,AA,55")
        target_temperature: int | None = None
        controller_time: datetime | None = None
        deadline = asyncio.get_running_loop().time() + 10
        while asyncio.get_running_loop().time() < deadline:
            messages, token = await self._async_subscribe(token)
            for message in messages:
                target, _ = parse_target_message(message)
                if target is not None:
                    target_temperature = target
                clock, _ = parse_clock_message(message, self._time_zone)
                if clock is not None:
                    controller_time = clock
            if target_temperature is not None and controller_time is not None:
                return target_temperature, controller_time
        raise WaterwayNeoCloudError("Timed out waiting for controller state")

    async def async_get_data(self) -> WaterwayNeoData:
        """Read the combined local and cloud state."""

        local = await self.async_get_local_status()
        target_temperature: int | None = None
        controller_time: datetime | None = None
        cloud_available = True
        try:
            target_temperature, controller_time = await self.async_read_cloud_state()
        except WaterwayNeoCloudError:
            cloud_available = False
        drift: float | None = None
        if controller_time is not None:
            drift = round(
                (controller_time - datetime.now(self._time_zone)).total_seconds() / 60,
                1,
            )
        return WaterwayNeoData(
            online=local.online,
            water_temperature=local.water_temperature,
            target_temperature=target_temperature,
            controller_time=controller_time,
            clock_drift_minutes=drift,
            cloud_available=cloud_available,
            raw_status=local.raw_status,
            other_status=local.other_status,
        )

    async def async_set_temperature(self, temperature: int) -> None:
        """Set the controller target temperature."""

        await self._async_publish(build_set_temperature_command(temperature))

    async def async_sync_time(self) -> datetime:
        """Set controller time and verify the echoed G2 response."""

        _, token = await self._async_subscribe("0")
        now = datetime.now(self._time_zone)
        await self._async_publish(build_set_time_command(now))
        deadline = asyncio.get_running_loop().time() + 10
        while asyncio.get_running_loop().time() < deadline:
            messages, token = await self._async_subscribe(token)
            for message in messages:
                confirmed, _ = parse_clock_message(message, self._time_zone)
                if confirmed is None:
                    continue
                if abs((confirmed - datetime.now(self._time_zone)).total_seconds()) > 120:
                    raise WaterwayNeoCloudError("Controller confirmed an unexpected time")
                return confirmed
        raise WaterwayNeoCloudError("Controller did not confirm the time update")
