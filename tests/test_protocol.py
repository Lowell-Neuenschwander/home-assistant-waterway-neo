"""Tests for the verified Waterway NEO protocol fields."""

import importlib.util
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

MODULE_PATH = Path(__file__).parents[1] / "custom_components" / "waterway_neo" / "protocol.py"
SPEC = importlib.util.spec_from_file_location("waterway_neo_protocol", MODULE_PATH)
assert SPEC and SPEC.loader
protocol = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = protocol
SPEC.loader.exec_module(protocol)


def test_parse_local_status() -> None:
    status = protocol.parse_local_status(
        "<response><ctrlstatus>$G0,0,00,00,00,10,64,00,!,AA,55</ctrlstatus>"
        "<ctrlother>$G8,0,00,!,AA,55</ctrlother></response>"
    )
    assert status.online is True
    assert status.water_temperature == 100
    assert status.other_status == "$G8,0,00,!,AA,55"


def test_parse_target_message() -> None:
    target, raw = protocol.parse_target_message({"OtherMsg": "$G7,0,63,!,AA,55"})
    assert target == 99
    assert raw == "$G7,0,63,!,AA,55"


def test_parse_clock_message() -> None:
    value, _ = protocol.parse_clock_message(
        {"OtherMsg": "$G2,0,26,07,28,02,16,57,45,!,AA,55"},
        ZoneInfo("America/Denver"),
    )
    assert value == datetime(2026, 7, 28, 16, 57, 45, tzinfo=ZoneInfo("America/Denver"))


def test_build_set_temperature_command() -> None:
    assert protocol.build_set_temperature_command(104) == "$S3,0,68,!,AA,55"
    with pytest.raises(ValueError):
        protocol.build_set_temperature_command(105)


def test_build_set_time_command() -> None:
    value = datetime(2026, 7, 28, 16, 57, 45, tzinfo=ZoneInfo("America/Denver"))
    assert protocol.build_set_time_command(value) == "$S6,1,D,26,07,28,W,2,T,16,57,00,!,AA,55"
