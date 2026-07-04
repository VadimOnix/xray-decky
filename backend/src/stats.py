"""
Traffic statistics via the xray-core StatsService.

The generated config enables the stats API on a localhost-only inbound;
totals are read with `xray api statsquery` (no extra gRPC dependencies)
and per-second speeds are derived by diffing successive samples.
"""

import asyncio
import json
import time
from typing import Any, Dict, Optional

API_PORT = 10085
_QUERY_TIMEOUT = 5.0

_UPLINK_KEY = "outbound>>>proxy>>>traffic>>>uplink"
_DOWNLINK_KEY = "outbound>>>proxy>>>traffic>>>downlink"


class TrafficStats:
    """Samples cumulative counters and computes speeds between samples."""

    def __init__(self) -> None:
        self._last: Optional[Dict[str, float]] = None

    def reset(self) -> None:
        """Forget the previous sample (call on connect/disconnect)."""
        self._last = None

    async def query_totals(
        self, xray_binary: str, api_port: int = API_PORT
    ) -> Optional[Dict[str, int]]:
        """Read cumulative uplink/downlink bytes; None if unavailable."""
        try:
            process = await asyncio.create_subprocess_exec(
                xray_binary,
                "api",
                "statsquery",
                f"--server=127.0.0.1:{api_port}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _stderr = await asyncio.wait_for(
                process.communicate(), timeout=_QUERY_TIMEOUT
            )
            if process.returncode != 0:
                return None
            data = json.loads(stdout.decode("utf-8", errors="ignore") or "{}")
        except (OSError, asyncio.TimeoutError, json.JSONDecodeError, ValueError):
            return None

        uplink = downlink = 0
        for item in data.get("stat", []):
            if not isinstance(item, dict):
                continue
            try:
                value = int(item.get("value") or 0)
            except (ValueError, TypeError):
                continue
            name = item.get("name", "")
            if name == _UPLINK_KEY:
                uplink = value
            elif name == _DOWNLINK_KEY:
                downlink = value
        return {"uplink": uplink, "downlink": downlink}

    async def sample(
        self,
        xray_binary: str,
        api_port: int = API_PORT,
        monotonic=time.monotonic,
    ) -> Optional[Dict[str, Any]]:
        """
        One stats sample: cumulative totals plus bytes/second computed
        against the previous sample. None if the stats API is unreachable.
        """
        totals = await self.query_totals(xray_binary, api_port)
        if totals is None:
            return None

        now = monotonic()
        uplink_speed = downlink_speed = 0
        if self._last is not None:
            elapsed = now - self._last["t"]
            if elapsed > 0:
                # Counters reset when xray restarts; clamp negative deltas.
                uplink_speed = int(
                    max(0, totals["uplink"] - self._last["up"]) / elapsed
                )
                downlink_speed = int(
                    max(0, totals["downlink"] - self._last["down"]) / elapsed
                )

        self._last = {
            "t": now,
            "up": float(totals["uplink"]),
            "down": float(totals["downlink"]),
        }
        return {
            "uplink": totals["uplink"],
            "downlink": totals["downlink"],
            "uplinkSpeed": uplink_speed,
            "downlinkSpeed": downlink_speed,
        }
