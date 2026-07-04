"""Tests for backend.src.latency (TCPing)."""

import asyncio

from backend.src import latency


def _serve_and_ping():
    async def scenario():
        server = await asyncio.start_server(
            lambda r, w: w.close(), "127.0.0.1", 0
        )
        port = server.sockets[0].getsockname()[1]
        try:
            return await latency.tcping("127.0.0.1", port, timeout=2.0), port
        finally:
            server.close()
            await server.wait_closed()

    return asyncio.run(scenario())


def test_tcping_reachable():
    ms, _port = _serve_and_ping()
    assert isinstance(ms, int)
    assert 0 <= ms < 2000


def test_tcping_unreachable():
    async def scenario():
        # Reserve a port and close it so nothing is listening.
        server = await asyncio.start_server(lambda r, w: w.close(), "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        server.close()
        await server.wait_closed()
        return await latency.tcping("127.0.0.1", port, timeout=1.0)

    assert asyncio.run(scenario()) is None


def test_test_profiles_maps_ids_and_skips_incomplete():
    async def scenario():
        server = await asyncio.start_server(lambda r, w: w.close(), "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        try:
            profiles = [
                {"id": "ok", "address": "127.0.0.1", "port": port},
                {"id": "incomplete", "address": "", "port": port},
                {"address": "127.0.0.1", "port": port},  # no id
            ]
            return await latency.test_profiles(profiles, timeout=2.0)
        finally:
            server.close()
            await server.wait_closed()

    results = asyncio.run(scenario())
    assert set(results.keys()) == {"ok"}
    assert isinstance(results["ok"], int)
