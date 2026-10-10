"""Tests for Waterway NEO client reliability behavior."""

import asyncio
import importlib.util
import sys
import types
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

try:
    import aiohttp  # noqa: F401
except ModuleNotFoundError:
    aiohttp = types.ModuleType("aiohttp")
    aiohttp.ClientError = type("ClientError", (Exception,), {})
    aiohttp.ClientSession = type("ClientSession", (), {})
    aiohttp.ClientTimeout = type("ClientTimeout", (), {})
    sys.modules["aiohttp"] = aiohttp

PACKAGE_PATH = Path(__file__).parents[1] / "custom_components" / "waterway_neo"
PACKAGE_NAME = "waterway_neo_test"
package = types.ModuleType(PACKAGE_NAME)
package.__path__ = [str(PACKAGE_PATH)]
sys.modules[PACKAGE_NAME] = package


def _load_module(name: str):
    spec = importlib.util.spec_from_file_location(
        f"{PACKAGE_NAME}.{name}", PACKAGE_PATH / f"{name}.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


const = types.ModuleType(f"{PACKAGE_NAME}.const")
const.PUBNUB_ORIGIN = "https://example.invalid"
const.PUBNUB_UUID = "test"
sys.modules[const.__name__] = const
protocol = _load_module("protocol")
api = _load_module("api")


class FakeClient(api.WaterwayNeoClient):
    """Waterway client with deterministic I/O."""

    def __init__(self) -> None:
        self.published: list[str] = []
        self.subscribe_responses: list[tuple[list[dict[str, str]], str]] = []
        self._time_zone = ZoneInfo("America/Denver")

    async def _async_subscribe(
        self, timetoken: str, *, timeout: int = 6
    ) -> tuple[list[dict[str, str]], str]:
        del timetoken, timeout
        return self.subscribe_responses.pop(0)

    async def _async_publish(self, command: str) -> None:
        self.published.append(command)


def test_set_temperature_requires_confirmation() -> None:
    client = FakeClient()
    client.subscribe_responses = [
        ([], "current"),
        ([{"OtherMsg": "$G7,0,63,!,AA,55"}], "confirmed"),
    ]

    asyncio.run(client.async_set_temperature(99, attempts=1))

    assert client.published == ["$S3,0,63,!,AA,55", "$G7,0,!,AA,55"]


def test_set_temperature_rejects_unconfirmed_command() -> None:
    client = FakeClient()
    client.subscribe_responses = [([], "current")]

    with pytest.raises(api.WaterwayNeoCloudError, match="did not confirm"):
        asyncio.run(client.async_set_temperature(99, attempts=1, confirmation_timeout=0))


def test_cloud_state_survives_local_connection_failure() -> None:
    class PartialClient(FakeClient):
        async def async_get_local_status(self):
            raise api.WaterwayNeoConnectionError("local unavailable")

        async def async_read_cloud_state(self):
            return 99, datetime(2026, 10, 10, 6, 0, tzinfo=self._time_zone)

    data = asyncio.run(PartialClient().async_get_data())

    assert data.online is False
    assert data.local_available is False
    assert data.water_temperature is None
    assert data.cloud_available is True
    assert data.target_temperature == 99
    assert data.local_error == "local unavailable"
    assert data.cloud_error is None


def test_local_state_survives_cloud_connection_failure() -> None:
    class PartialClient(FakeClient):
        async def async_get_local_status(self):
            return protocol.LocalStatus(True, 100, "$G0,0,00,00,00,10,64,00,!,AA,55", "")

        async def async_read_cloud_state(self):
            raise api.WaterwayNeoCloudError("cloud unavailable")

    data = asyncio.run(PartialClient().async_get_data())

    assert data.online is True
    assert data.local_available is True
    assert data.water_temperature == 100
    assert data.cloud_available is False
    assert data.target_temperature is None
    assert data.local_error is None
    assert data.cloud_error == "cloud unavailable"
