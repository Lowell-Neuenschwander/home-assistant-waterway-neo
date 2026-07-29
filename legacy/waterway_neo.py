#!/usr/bin/env python3
"""Standalone Waterway NEO helper for the legacy Home Assistant package.

Configuration is read from /config/waterway_neo_config.json by default. The
configuration file must not be committed or shared.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_CONFIG = "/config/waterway_neo_config.json"
PUBNUB_ORIGIN = "https://ps9.pubnub.com"
UUID = "home-assistant-waterway-neo-legacy"
MIN_TEMP_F = 80
MAX_TEMP_F = 104


class Client:
    """Small dependency-free Waterway NEO client."""

    def __init__(self, config: dict[str, object]) -> None:
        self.host = str(config["host"]).removeprefix("http://").rstrip("/")
        self.publish_key = str(config["publish_key"])
        self.subscribe_key = str(config["subscribe_key"])
        self.channel = str(config["channel"])
        self.time_zone = ZoneInfo(str(config.get("time_zone", "UTC")))

    @staticmethod
    def _fetch_json(url: str, timeout: int = 8) -> object:
        request = urllib.request.Request(
            url, headers={"User-Agent": "HomeAssistant-WaterwayNEO-Legacy/0.1"}
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())

    def subscribe(self, timetoken: str, timeout: int = 6) -> tuple[list[dict], str]:
        url = (
            f"{PUBNUB_ORIGIN}/subscribe/{urllib.parse.quote(self.subscribe_key)}/"
            f"{urllib.parse.quote(self.channel)}/0/{timetoken}?uuid={UUID}"
        )
        payload = self._fetch_json(url, timeout)
        if not isinstance(payload, list) or len(payload) < 2:
            raise RuntimeError("unexpected subscribe response")
        return [item for item in payload[0] if isinstance(item, dict)], str(payload[1])

    def publish(self, command: str) -> None:
        message = urllib.parse.quote(json.dumps({"cmd": command}, separators=(",", ":")), safe="")
        url = (
            f"{PUBNUB_ORIGIN}/publish/{urllib.parse.quote(self.publish_key)}/"
            f"{urllib.parse.quote(self.subscribe_key)}/0/"
            f"{urllib.parse.quote(self.channel)}/0/{message}?uuid={UUID}"
        )
        payload = self._fetch_json(url)
        if not isinstance(payload, list) or not payload or payload[0] != 1:
            raise RuntimeError("controller command rejected")

    def read_local(self) -> tuple[str, str, int | None]:
        from xml.etree import ElementTree

        with urllib.request.urlopen(f"http://{self.host}/status.xml", timeout=8) as response:
            root = ElementTree.fromstring(response.read())
        raw = (root.findtext("ctrlstatus") or "").strip()
        other = (root.findtext("ctrlother") or "").strip()
        fields = raw.split(",")
        temperature = int(fields[6], 16) if len(fields) > 6 else None
        return raw, other, temperature

    def read_cloud(self) -> tuple[int | None, datetime | None]:
        _, token = self.subscribe("0")
        self.publish("$G7,0,!,AA,55")
        self.publish("$G2,0,!,AA,55")
        target = None
        clock = None
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            messages, token = self.subscribe(token)
            for message in messages:
                raw = str(message.get("OtherMsg", ""))
                fields = raw.split(",")
                if len(fields) >= 3 and fields[0] in ("$G7", "$A7"):
                    candidate = fields[-4] if fields[0] == "$A7" else fields[2]
                    value = int(candidate, 16)
                    if MIN_TEMP_F <= value <= MAX_TEMP_F:
                        target = value
                if len(fields) >= 12 and fields[0] in ("$G2", "$A2"):
                    clock = datetime(
                        2000 + int(fields[2]),
                        int(fields[3]),
                        int(fields[4]),
                        int(fields[6]),
                        int(fields[7]),
                        int(fields[8]),
                        tzinfo=self.time_zone,
                    )
            if target is not None and clock is not None:
                return target, clock
        raise RuntimeError("timed out waiting for controller state")

    def status(self) -> dict[str, object]:
        raw, other, water = self.read_local()
        target, clock = self.read_cloud()
        drift = (
            round((clock - datetime.now(self.time_zone)).total_seconds() / 60, 1) if clock else None
        )
        return {
            "status": "online" if raw.startswith("$G0,") else "invalid",
            "water_temperature": water,
            "target_temperature": target,
            "controller_time": clock.isoformat() if clock else None,
            "clock_drift_minutes": drift,
            "raw_status": raw,
            "other_status": other,
        }

    def set_temperature(self, temperature: int) -> None:
        if not MIN_TEMP_F <= temperature <= MAX_TEMP_F:
            raise ValueError(f"temperature must be {MIN_TEMP_F}-{MAX_TEMP_F} F")
        self.publish(f"$S3,0,{temperature:02X},!,AA,55")

    def sync_time(self) -> None:
        now = datetime.now(self.time_zone)
        weekday = int(now.strftime("%w"))
        self.publish(
            f"$S6,1,D,{now.year % 100:02d},{now.month:02d},{now.day:02d},"
            f"W,{weekday},T,{now.hour:02d},{now.minute:02d},00,!,AA,55"
        )


def load_config(path: str) -> dict[str, object]:
    with Path(path).open(encoding="utf-8") as config_file:
        return json.load(config_file)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("status")
    set_parser = subparsers.add_parser("set")
    set_parser.add_argument("temperature", type=int)
    subparsers.add_parser("sync-time")
    args = parser.parse_args()
    client = Client(load_config(args.config))
    if args.command in (None, "status"):
        print(json.dumps(client.status()))
    elif args.command == "set":
        client.set_temperature(args.temperature)
        print(json.dumps({"status": "sent", "temperature": args.temperature}))
    elif args.command == "sync-time":
        client.sync_time()
        print(json.dumps({"status": "sent"}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "offline", "error": type(exc).__name__}))
        raise SystemExit(1) from exc
