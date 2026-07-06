"""
Latency testing for server profiles.

First cut per the roadmap: TCPing — time to establish a TCP connection to
the server's address:port. Cheap, no running core required, good enough to
rank servers. Real-delay tests through the proxy come later.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

DEFAULT_TIMEOUT = 3.0
DEFAULT_CONCURRENCY = 8


async def tcping(
    address: str, port: int, timeout: float = DEFAULT_TIMEOUT
) -> Optional[int]:
    """
    Measure TCP connect time in milliseconds. Returns None if unreachable
    within the timeout.
    """
    start = time.monotonic()
    try:
        _reader, writer = await asyncio.wait_for(
            asyncio.open_connection(address, port), timeout=timeout
        )
    except (OSError, asyncio.TimeoutError):
        return None
    elapsed_ms = int((time.monotonic() - start) * 1000)
    writer.close()
    try:
        await writer.wait_closed()
    except OSError:
        pass
    return elapsed_ms


async def test_profiles(
    profiles: List[Dict[str, Any]],
    timeout: float = DEFAULT_TIMEOUT,
    concurrency: int = DEFAULT_CONCURRENCY,
) -> Dict[str, Optional[int]]:
    """
    TCPing every profile concurrently (bounded). Returns {id: ms | None}.
    Profiles without id/address/port are skipped.
    """
    semaphore = asyncio.Semaphore(concurrency)
    results: Dict[str, Optional[int]] = {}

    async def probe(profile: Dict[str, Any]) -> None:
        profile_id = profile.get("id")
        address = profile.get("address")
        port = profile.get("port")
        if not profile_id or not address or not port:
            return
        async with semaphore:
            results[profile_id] = await tcping(address, int(port), timeout)

    await asyncio.gather(*(probe(p) for p in profiles))
    return results
