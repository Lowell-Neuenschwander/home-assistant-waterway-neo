"""Tests for the dependency-free legacy helper."""

import importlib.util
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

MODULE_PATH = Path(__file__).parents[1] / "legacy" / "waterway_neo.py"
SPEC = importlib.util.spec_from_file_location("waterway_neo_legacy", MODULE_PATH)
assert SPEC and SPEC.loader
legacy = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = legacy
SPEC.loader.exec_module(legacy)


class FakeClient(legacy.Client):
    """Legacy client with deterministic I/O."""

    def __init__(self) -> None:
        self.published: list[str] = []
        self.subscribe_responses: list[tuple[list[dict[str, str]], str]] = []
        self.time_zone = ZoneInfo("America/Denver")

    def subscribe(self, timetoken: str, timeout: int = 6):
        del timetoken, timeout
        return self.subscribe_responses.pop(0)

    def publish(self, command: str) -> None:
        self.published.append(command)


def test_legacy_set_temperature_requires_confirmation() -> None:
    client = FakeClient()
    client.subscribe_responses = [
        ([], "current"),
        ([{"OtherMsg": "$G7,0,63,!,AA,55"}], "confirmed"),
    ]

    client.set_temperature(99, attempts=1)

    assert client.published == ["$S3,0,63,!,AA,55", "$G7,0,!,AA,55"]


def test_legacy_set_temperature_rejects_bad_value() -> None:
    with pytest.raises(ValueError):
        FakeClient().set_temperature(105)


def test_legacy_cloud_state_survives_local_failure() -> None:
    class PartialClient(FakeClient):
        def read_local(self):
            raise TimeoutError

        def read_cloud(self):
            return 99, datetime(2026, 10, 10, 6, 0, tzinfo=self.time_zone)

    data = PartialClient().status()

    assert data["status"] == "invalid"
    assert data["local_available"] is False
    assert data["cloud_available"] is True
    assert data["target_temperature"] == 99
    assert data["local_error"] == "TimeoutError"


def test_legacy_local_state_survives_cloud_failure() -> None:
    class PartialClient(FakeClient):
        def read_local(self):
            return "$G0,0,00,00,00,10,64,00,!,AA,55", "", 100

        def read_cloud(self):
            raise TimeoutError

    data = PartialClient().status()

    assert data["status"] == "online"
    assert data["local_available"] is True
    assert data["water_temperature"] == 100
    assert data["cloud_available"] is False
    assert data["cloud_error"] == "TimeoutError"
