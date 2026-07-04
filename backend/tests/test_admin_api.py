"""Tests for backend.src.admin_api (token auth + REST endpoints)."""

import asyncio
from pathlib import Path

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from backend.src.admin_api import (
    RateLimiter,
    config_summary,
    ensure_admin_token,
    register_admin_routes,
)


TOKEN = "test-token-123"


class _Clock:
    """Manually-advanced clock for deterministic RateLimiter tests."""

    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


class _FakeSettings:
    def __init__(self, initial=None):
        self.data = dict(initial or {})
        self.commits = 0

    def getSetting(self, key, default=None):
        return self.data.get(key, default)

    def setSetting(self, key, value):
        self.data[key] = value

    def commit(self):
        self.commits += 1


def _make_handlers(overrides=None):
    calls = []

    def handler(name, result):
        async def _h(*args):
            calls.append((name, args))
            return dict(result)

        return _h

    handlers = {
        "get_connection_status": handler("status", {"status": "disconnected"}),
        "toggle_connection": handler("toggle_connection", {"success": True}),
        "get_vless_config": handler("get_config", {"config": None}),
        "import_config": handler("import", {"success": True}),
        "toggle_tun_mode": handler("tun", {"success": True}),
        "toggle_kill_switch": handler("killswitch", {"success": True}),
        "deactivate_kill_switch": handler("deactivate", {"success": True}),
        "get_profiles": handler(
            "get_profiles",
            {
                "success": True,
                "activeId": "p1",
                "profiles": [
                    {
                        "id": "p1",
                        "protocol": "trojan",
                        "address": "example.com",
                        "port": 443,
                        "password": "secret",
                        "latencyMs": 42,
                    }
                ],
            },
        ),
        "set_active_profile": handler("set_active_profile", {"success": True}),
        "remove_profile": handler("remove_profile", {"success": True}),
        "test_profiles_latency": handler(
            "test_profiles_latency", {"success": True, "results": {"p1": 42}}
        ),
        "refresh_subscription": handler(
            "refresh_subscription", {"success": True, "profileCount": 3}
        ),
        "get_traffic_stats": handler(
            "get_traffic_stats",
            {
                "success": True,
                "available": True,
                "uplink": 10,
                "downlink": 20,
                "uplinkSpeed": 1,
                "downlinkSpeed": 2,
            },
        ),
        "check_updates": handler(
            "check_updates",
            {
                "success": True,
                "components": [
                    {
                        "name": "xray-decky",
                        "kind": "plugin",
                        "current": "1.0.1",
                        "latest": "v1.0.1",
                        "updateAvailable": False,
                    },
                    {
                        "name": "xray-core",
                        "kind": "core",
                        "current": "v26.3.27",
                        "latest": "v26.3.27",
                        "updateAvailable": False,
                    },
                ],
            },
        ),
    }
    handlers.update(overrides or {})
    return handlers, calls


def _run(coro):
    return asyncio.run(coro)


async def _client(settings=None, handlers=None, static_dir=None, rate_limiter=None):
    app = web.Application()
    register_admin_routes(
        app,
        settings=settings or _FakeSettings(),
        static_dir=static_dir or Path("/nonexistent"),
        handlers=handlers or _make_handlers()[0],
        token=TOKEN,
        rate_limiter=rate_limiter,
    )
    client = TestClient(TestServer(app))
    await client.start_server()
    return client


def test_ensure_admin_token_generates_and_persists():
    settings = _FakeSettings()
    token = ensure_admin_token(settings)
    assert token and len(token) >= 16
    assert settings.commits == 1
    # Second call returns the same token without regenerating.
    assert ensure_admin_token(settings) == token
    assert settings.commits == 1


def test_config_summary_redacts_credentials():
    summary = config_summary(
        {
            "protocol": "trojan",
            "password": "secret",
            "uuid": "abc",
            "address": "example.com",
            "port": 443,
            "network": "ws",
            "security": "tls",
            "sourceUrl": "trojan://secret@example.com:443",
            "transport": {"path": "/x"},
        }
    )
    assert summary == {
        "protocol": "trojan",
        "address": "example.com",
        "port": 443,
        "network": "ws",
        "security": "tls",
    }
    assert config_summary(None) is None


def test_status_requires_token():
    async def scenario():
        client = await _client()
        try:
            resp = await client.get("/api/v1/status")
            assert resp.status == 401
            resp = await client.get(
                "/api/v1/status", headers={"X-Admin-Token": "wrong"}
            )
            assert resp.status == 401
            resp = await client.get(
                "/api/v1/status", headers={"X-Admin-Token": TOKEN}
            )
            assert resp.status == 200
            data = await resp.json()
            assert data["success"] is True
            assert data["connection"]["status"] == "disconnected"
        finally:
            await client.close()

    _run(scenario())


def test_status_accepts_query_token_and_reports_prefs():
    settings = _FakeSettings(
        {
            "tunMode": {"enabled": True, "hasPrivileges": False},
            "killSwitch": {"enabled": True, "isActive": True},
        }
    )

    async def scenario():
        client = await _client(settings=settings)
        try:
            resp = await client.get("/api/v1/status", params={"token": TOKEN})
            assert resp.status == 200
            data = await resp.json()
            assert data["tun"] == {"enabled": True, "hasPrivileges": False}
            assert data["killSwitch"] == {"enabled": True, "isActive": True}
        finally:
            await client.close()

    _run(scenario())


def test_connection_toggle_calls_handler():
    handlers, calls = _make_handlers()

    async def scenario():
        client = await _client(handlers=handlers)
        try:
            resp = await client.post(
                "/api/v1/connection",
                json={"enable": True},
                headers={"X-Admin-Token": TOKEN},
            )
            assert resp.status == 200
            assert ("toggle_connection", (True,)) in calls

            # Invalid bodies rejected before reaching the handler.
            resp = await client.post(
                "/api/v1/connection",
                json={"enable": "yes"},
                headers={"X-Admin-Token": TOKEN},
            )
            assert resp.status == 400
            resp = await client.post(
                "/api/v1/connection",
                data=b"not json",
                headers={"X-Admin-Token": TOKEN},
            )
            assert resp.status == 400
        finally:
            await client.close()

    _run(scenario())


def test_mutating_endpoints_require_token():
    handlers, calls = _make_handlers()

    async def scenario():
        client = await _client(handlers=handlers)
        try:
            for path, body in (
                ("/api/v1/connection", {"enable": True}),
                ("/api/v1/tun", {"enabled": True}),
                ("/api/v1/killswitch", {"enabled": True}),
                ("/api/v1/killswitch/deactivate", None),
                ("/api/v1/import", {"link": "vless://x"}),
            ):
                resp = await client.post(path, json=body)
                assert resp.status == 401, path
            assert calls == []
        finally:
            await client.close()

    _run(scenario())


def test_handler_failure_maps_to_error_status():
    async def failing(*_args):
        return {"success": False, "error": "boom"}

    handlers, _ = _make_handlers({"toggle_connection": failing})

    async def scenario():
        client = await _client(handlers=handlers)
        try:
            resp = await client.post(
                "/api/v1/connection",
                json={"enable": True},
                headers={"X-Admin-Token": TOKEN},
            )
            assert resp.status == 502
            data = await resp.json()
            assert data["error"] == "boom"
        finally:
            await client.close()

    _run(scenario())


def test_import_endpoint_validates_and_calls_handler():
    handlers, calls = _make_handlers()

    async def scenario():
        client = await _client(handlers=handlers)
        try:
            resp = await client.post(
                "/api/v1/import",
                json={"link": "  vless://x  "},
                headers={"X-Admin-Token": TOKEN},
            )
            assert resp.status == 200
            assert ("import", ("vless://x",)) in calls

            resp = await client.post(
                "/api/v1/import",
                json={"link": ""},
                headers={"X-Admin-Token": TOKEN},
            )
            assert resp.status == 400
        finally:
            await client.close()

    _run(scenario())


def test_profiles_endpoint_redacts_credentials():
    async def scenario():
        client = await _client()
        try:
            resp = await client.get(
                "/api/v1/profiles", headers={"X-Admin-Token": TOKEN}
            )
            assert resp.status == 200
            data = await resp.json()
            assert data["activeId"] == "p1"
            profile = data["profiles"][0]
            assert profile["id"] == "p1"
            assert profile["latencyMs"] == 42
            assert "password" not in profile
        finally:
            await client.close()

    _run(scenario())


def test_profile_activate_remove_and_ping():
    handlers, calls = _make_handlers()

    async def scenario():
        client = await _client(handlers=handlers)
        try:
            resp = await client.post(
                "/api/v1/profiles/activate",
                json={"id": "p2"},
                headers={"X-Admin-Token": TOKEN},
            )
            assert resp.status == 200
            assert ("set_active_profile", ("p2",)) in calls

            resp = await client.post(
                "/api/v1/profiles/remove",
                json={"id": "p1"},
                headers={"X-Admin-Token": TOKEN},
            )
            assert resp.status == 200
            assert ("remove_profile", ("p1",)) in calls

            # Missing/invalid id rejected before the handler runs.
            resp = await client.post(
                "/api/v1/profiles/activate",
                json={"id": 5},
                headers={"X-Admin-Token": TOKEN},
            )
            assert resp.status == 400

            resp = await client.post(
                "/api/v1/profiles/ping", headers={"X-Admin-Token": TOKEN}
            )
            assert resp.status == 200
            data = await resp.json()
            assert data["results"] == {"p1": 42}

            resp = await client.post(
                "/api/v1/subscription/refresh", headers={"X-Admin-Token": TOKEN}
            )
            assert resp.status == 200
            assert ("refresh_subscription", ()) in calls

            resp = await client.get(
                "/api/v1/stats", headers={"X-Admin-Token": TOKEN}
            )
            assert resp.status == 200
            data = await resp.json()
            assert data["downlinkSpeed"] == 2
            resp = await client.get("/api/v1/stats")
            assert resp.status == 401

            # All profile endpoints require the token.
            for path in (
                "/api/v1/profiles/activate",
                "/api/v1/profiles/remove",
                "/api/v1/profiles/ping",
                "/api/v1/subscription/refresh",
            ):
                resp = await client.post(path, json={"id": "x"})
                assert resp.status == 401, path
            resp = await client.get("/api/v1/profiles")
            assert resp.status == 401
        finally:
            await client.close()

    _run(scenario())


def test_updates_endpoint():
    async def scenario():
        client = await _client()
        try:
            resp = await client.get("/api/v1/updates", headers={"X-Admin-Token": TOKEN})
            assert resp.status == 200
            data = await resp.json()
            assert data["components"][0]["name"] == "xray-decky"
            assert data["components"][0]["updateAvailable"] is False
            # Token required.
            resp = await client.get("/api/v1/updates")
            assert resp.status == 401
        finally:
            await client.close()

    _run(scenario())


def test_rate_limiter_locks_out_and_expires():
    clock = _Clock()
    rl = RateLimiter(max_failures=3, window=60, block=30, clock=clock)
    key = "1.2.3.4"
    assert not rl.is_blocked(key)
    rl.record_failure(key)
    rl.record_failure(key)
    assert not rl.is_blocked(key)  # two failures, still under the limit
    rl.record_failure(key)  # third failure trips the lockout
    assert rl.is_blocked(key)
    assert rl.retry_after(key) >= 1
    clock.advance(30)  # cooldown elapses
    assert not rl.is_blocked(key)
    assert rl.retry_after(key) == 0


def test_rate_limiter_window_slides():
    clock = _Clock()
    rl = RateLimiter(max_failures=3, window=10, block=30, clock=clock)
    key = "k"
    rl.record_failure(key)
    clock.advance(4)
    rl.record_failure(key)
    clock.advance(8)  # the first failure is now older than the window
    rl.record_failure(key)  # only two failures fall inside the window
    assert not rl.is_blocked(key)


def test_rate_limiter_success_resets():
    clock = _Clock()
    rl = RateLimiter(max_failures=3, window=60, block=60, clock=clock)
    key = "k"
    rl.record_failure(key)
    rl.record_failure(key)
    rl.record_success(key)  # a valid token wipes the history
    rl.record_failure(key)
    rl.record_failure(key)
    assert not rl.is_blocked(key)


def test_auth_rate_limited_after_repeated_failures():
    rl = RateLimiter(max_failures=3, window=60, block=60)

    async def scenario():
        client = await _client(rate_limiter=rl)
        try:
            for _ in range(3):
                resp = await client.get(
                    "/api/v1/status", headers={"X-Admin-Token": "wrong"}
                )
                assert resp.status == 401
            # Locked out now — even the correct token is refused with 429.
            resp = await client.get(
                "/api/v1/status", headers={"X-Admin-Token": TOKEN}
            )
            assert resp.status == 429
            assert int(resp.headers.get("Retry-After", "0")) >= 1
        finally:
            await client.close()

    _run(scenario())


def test_auth_success_avoids_lockout():
    rl = RateLimiter(max_failures=3, window=60, block=60)

    async def scenario():
        client = await _client(rate_limiter=rl)
        try:
            # Interleaved successes keep the failure counter from saturating.
            for _ in range(5):
                bad = await client.get(
                    "/api/v1/status", headers={"X-Admin-Token": "wrong"}
                )
                assert bad.status == 401
                ok = await client.get(
                    "/api/v1/status", headers={"X-Admin-Token": TOKEN}
                )
                assert ok.status == 200
        finally:
            await client.close()

    _run(scenario())


def test_admin_page_served_without_token(tmp_path: Path):
    (tmp_path / "admin.html").write_text("<html>admin</html>")

    async def scenario():
        client = await _client(static_dir=tmp_path)
        try:
            resp = await client.get("/admin")
            assert resp.status == 200
            text = await resp.text()
            assert "admin" in text
        finally:
            await client.close()

    _run(scenario())
