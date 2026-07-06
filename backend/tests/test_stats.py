"""Tests for backend.src.stats (statsquery parsing + speed computation)."""

import asyncio
import json
from unittest.mock import patch

from backend.src.stats import TrafficStats


class _FakeProcess:
    def __init__(self, returncode: int, stdout: bytes):
        self.returncode = returncode
        self._stdout = stdout

    async def communicate(self):
        return self._stdout, b""


def _statsquery_output(uplink, downlink):
    return json.dumps(
        {
            "stat": [
                {"name": "outbound>>>proxy>>>traffic>>>uplink", "value": str(uplink)},
                {
                    "name": "outbound>>>proxy>>>traffic>>>downlink",
                    "value": str(downlink),
                },
                {"name": "outbound>>>direct>>>traffic>>>uplink", "value": "999999"},
            ]
        }
    ).encode()


def _patch_exec(process):
    async def fake_exec(*_args, **_kwargs):
        return process

    return patch("asyncio.create_subprocess_exec", fake_exec)


def test_query_totals_parses_proxy_counters_only():
    stats = TrafficStats()
    with _patch_exec(_FakeProcess(0, _statsquery_output(100, 2000))):
        totals = asyncio.run(stats.query_totals("/bin/xray"))
    assert totals == {"uplink": 100, "downlink": 2000}


def test_query_totals_failures():
    stats = TrafficStats()
    with _patch_exec(_FakeProcess(1, b"")):
        assert asyncio.run(stats.query_totals("/bin/xray")) is None
    with _patch_exec(_FakeProcess(0, b"not json")):
        assert asyncio.run(stats.query_totals("/bin/xray")) is None


def test_sample_computes_speeds_between_samples():
    stats = TrafficStats()
    clock = {"t": 100.0}

    def monotonic():
        return clock["t"]

    async def scenario():
        with _patch_exec(_FakeProcess(0, _statsquery_output(1000, 5000))):
            first = await stats.sample("/bin/xray", monotonic=monotonic)
        clock["t"] += 2.0
        with _patch_exec(_FakeProcess(0, _statsquery_output(3000, 15000))):
            second = await stats.sample("/bin/xray", monotonic=monotonic)
        return first, second

    first, second = asyncio.run(scenario())
    # First sample has no baseline: zero speeds.
    assert first["uplinkSpeed"] == 0
    assert first["downlinkSpeed"] == 0
    # (3000-1000)/2s and (15000-5000)/2s
    assert second["uplinkSpeed"] == 1000
    assert second["downlinkSpeed"] == 5000
    assert second["uplink"] == 3000
    assert second["downlink"] == 15000


def test_sample_clamps_counter_reset_and_reset_clears_baseline():
    stats = TrafficStats()
    clock = {"t": 0.0}

    def monotonic():
        return clock["t"]

    async def scenario():
        with _patch_exec(_FakeProcess(0, _statsquery_output(5000, 5000))):
            await stats.sample("/bin/xray", monotonic=monotonic)
        clock["t"] += 1.0
        # xray restarted: counters went backwards -> speeds clamp to 0.
        with _patch_exec(_FakeProcess(0, _statsquery_output(100, 100))):
            after_reset = await stats.sample("/bin/xray", monotonic=monotonic)

        stats.reset()
        clock["t"] += 1.0
        with _patch_exec(_FakeProcess(0, _statsquery_output(200, 200))):
            fresh = await stats.sample("/bin/xray", monotonic=monotonic)
        return after_reset, fresh

    after_reset, fresh = asyncio.run(scenario())
    assert after_reset["uplinkSpeed"] == 0
    assert after_reset["downlinkSpeed"] == 0
    # After reset() the next sample has no baseline again.
    assert fresh["uplinkSpeed"] == 0
