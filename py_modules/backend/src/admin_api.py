"""
Admin panel: REST API + static SPA served by the embedded aiohttp server.

Registers /admin (web UI) and /api/v1/* (JSON API) on the existing import
server app, so the panel shares the HTTPS port and self-signed cert.

Security model (DeckyClash-style): a random per-install token is generated
on first start and stored in settings. Every /api/v1/* request must present
it via the X-Admin-Token header or a ?token= query parameter. The QAM shows
the panel URL with the token embedded as a QR code.
"""

import json
import secrets
import time
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional

from aiohttp import web


Handler = Callable[..., Awaitable[Dict[str, Any]]]

# Auth rate limiting: after this many failed attempts from one client within
# the window, lock that client out for the cooldown. Legitimate use (a browser
# with the right token) never accumulates failures, so honest clients are
# unaffected; this only slows down token brute-forcing over the LAN.
_MAX_AUTH_FAILURES = 15
_AUTH_WINDOW_SECONDS = 60.0
_AUTH_BLOCK_SECONDS = 60.0
# Cap on tracked client keys. Every distinct source address that fails auth
# adds an entry, and a client that never comes back never triggers the
# success/expiry paths that drop it — so without a cap, a LAN peer cycling
# source addresses grows these dicts without bound. Well above the number of
# devices on any real home network.
_MAX_TRACKED_CLIENTS = 1024


class RateLimiter:
    """In-memory per-client failure limiter with a sliding window + lockout.

    Not shared across installs or persisted — a plugin reload clears it, which
    is fine for a brute-force speed bump. ``clock`` is injectable for testing.
    """

    def __init__(
        self,
        max_failures: int = _MAX_AUTH_FAILURES,
        window: float = _AUTH_WINDOW_SECONDS,
        block: float = _AUTH_BLOCK_SECONDS,
        clock: Callable[[], float] = time.monotonic,
        max_clients: int = _MAX_TRACKED_CLIENTS,
    ) -> None:
        self._max = max_failures
        self._window = window
        self._block = block
        self._clock = clock
        self._max_clients = max_clients
        self._failures: Dict[str, List[float]] = {}
        self._blocked_until: Dict[str, float] = {}

    def is_blocked(self, key: str) -> bool:
        """True while the client is locked out; clears state once it expires."""
        until = self._blocked_until.get(key)
        if until is None:
            return False
        if self._clock() >= until:
            self._blocked_until.pop(key, None)
            self._failures.pop(key, None)
            return False
        return True

    def record_failure(self, key: str) -> None:
        """Log a failed attempt; start a lockout once the window is saturated."""
        now = self._clock()
        recent = [t for t in self._failures.get(key, []) if now - t < self._window]
        recent.append(now)
        self._failures[key] = recent
        if len(recent) >= self._max:
            self._blocked_until[key] = now + self._block
        self._evict_stale(now)

    def tracked_clients(self) -> int:
        """Number of client keys currently held (for tests and diagnostics)."""
        return len(self._failures)

    def _drop(self, key: str) -> None:
        self._failures.pop(key, None)
        self._blocked_until.pop(key, None)

    def _evict_stale(self, now: float) -> None:
        """Enforce the tracked-client cap. Only runs on overflow.

        Two passes, in order of how little the entry is worth keeping:

        1. Entries whose window *and* lockout have both elapsed. These carry no
           information at all — dropping one cannot un-block a client or forgive
           a failure that still counts.
        2. If that was not enough (a genuine flood from many addresses inside a
           single window), the shortest live streaks, oldest first. A key one
           failure from lockout is the most valuable thing in the table, so it
           is the last to go; blocked keys are never evicted, because forgetting
           one would hand the attacker a free reset.
        """
        if len(self._failures) <= self._max_clients:
            return
        for key, times in list(self._failures.items()):
            if self._blocked_until.get(key, 0.0) > now:
                continue
            if not times or now - times[-1] >= self._window:
                self._drop(key)
        overflow = len(self._failures) - self._max_clients
        if overflow <= 0:
            return
        evictable = [k for k in self._failures if self._blocked_until.get(k, 0.0) <= now]
        evictable.sort(key=lambda k: (len(self._failures[k]), self._failures[k][-1]))
        for key in evictable[:overflow]:
            self._drop(key)

    def record_success(self, key: str) -> None:
        """A valid token clears the client's failure history."""
        self._drop(key)

    def retry_after(self, key: str) -> int:
        """Whole seconds until the lockout lifts (for the Retry-After header)."""
        until = self._blocked_until.get(key)
        if until is None:
            return 0
        return max(0, int(until - self._clock()) + 1)

# Profile fields safe to show in the panel (never credentials).
_SUMMARY_FIELDS = (
    "id",
    "protocol",
    "core",
    "name",
    "address",
    "port",
    "network",
    "security",
    "configType",
    "importedAt",
    "isValid",
    "latencyMs",
    "latencyTestedAt",
)


def ensure_admin_token(settings) -> str:
    """Return the per-install admin token, generating it on first use."""
    admin_config = settings.getSetting("adminPanel", {})
    token = admin_config.get("token")
    if not token or not isinstance(token, str):
        token = secrets.token_urlsafe(16)
        admin_config["token"] = token
        settings.setSetting("adminPanel", admin_config)
        settings.commit()
    return token


def lan_access_enabled(settings) -> bool:
    """Whether the panel/import server may bind to the LAN (default: yes).

    Defaults to True to preserve the historical behavior (QR pairing from a
    phone is the primary flow); the QAM offers an explicit toggle to restrict
    the server to localhost. Anything malformed falls back to the default.
    """
    admin_config = settings.getSetting("adminPanel", {})
    if not isinstance(admin_config, dict):
        return True
    value = admin_config.get("allowLan", True)
    return value if isinstance(value, bool) else True


def save_lan_access(settings, enabled: bool) -> None:
    """Persist the LAN-access preference (see lan_access_enabled)."""
    admin_config = settings.getSetting("adminPanel", {})
    if not isinstance(admin_config, dict):
        admin_config = {}
    admin_config["allowLan"] = bool(enabled)
    settings.setSetting("adminPanel", admin_config)
    settings.commit()


def admin_bind_host(settings) -> str:
    """The host the embedded HTTPS server should bind to."""
    return "0.0.0.0" if lan_access_enabled(settings) else "127.0.0.1"


def config_summary(config: Any) -> Dict[str, Any] | None:
    """Redact a stored profile down to displayable fields (no credentials)."""
    if not isinstance(config, dict):
        return None
    return {key: config[key] for key in _SUMMARY_FIELDS if key in config}


def register_admin_routes(
    app: web.Application,
    settings,
    static_dir: Path,
    handlers: Dict[str, Handler],
    token: str,
    rate_limiter: Optional[RateLimiter] = None,
) -> None:
    """
    Register admin panel routes on an existing aiohttp app.

    Args:
        app: The import server app (shares port + TLS).
        settings: SettingsManager instance.
        static_dir: Path to backend/static (admin.html/admin.css/admin.js).
        handlers: Async callables provided by the plugin:
            get_connection_status, toggle_connection, get_vless_config,
            import_config, toggle_tun_mode, toggle_kill_switch,
            deactivate_kill_switch, get_profiles, set_active_profile,
            remove_profile, test_profiles_latency, refresh_subscription,
            rename_subscription, set_subscription_refresh_interval,
            get_traffic_stats, check_updates, export_profiles.
        token: The admin token (see ensure_admin_token).
        rate_limiter: Failed-auth limiter; a fresh per-install one is created
            when omitted (state is per app, never shared across installs).
    """
    limiter = rate_limiter if rate_limiter is not None else RateLimiter()

    def _client_key(request: web.Request) -> str:
        return request.remote or "unknown"

    def _unauthorized() -> web.Response:
        return web.json_response(
            {"success": False, "error": "Invalid or missing admin token"},
            status=401,
        )

    def _guard(request: web.Request) -> Optional[web.Response]:
        """Authorize a request; None means allowed, otherwise the error to send.

        Returns 429 while the client is locked out, 401 on a bad/missing token
        (and records the failure), None on success (and clears the counter).
        """
        key = _client_key(request)
        if limiter.is_blocked(key):
            return web.json_response(
                {"success": False, "error": "Too many attempts — try again shortly"},
                status=429,
                headers={"Retry-After": str(limiter.retry_after(key))},
            )
        presented = request.headers.get("X-Admin-Token") or request.query.get(
            "token", ""
        )
        if presented and secrets.compare_digest(presented, token):
            limiter.record_success(key)
            return None
        limiter.record_failure(key)
        return _unauthorized()

    async def _body_json(request: web.Request) -> Dict[str, Any] | None:
        try:
            body = await request.json()
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        return body if isinstance(body, dict) else None

    async def get_admin_page(_request: web.Request) -> web.StreamResponse:
        html_path = static_dir / "admin.html"
        if not html_path.is_file():
            return web.Response(status=404, text="admin.html not found")
        return web.FileResponse(html_path, headers={"Content-Type": "text/html"})

    async def api_status(request: web.Request) -> web.Response:
        denied = _guard(request)
        if denied is not None:
            return denied
        connection = await handlers["get_connection_status"]()
        config_result = await handlers["get_vless_config"]()
        tun_pref = settings.getSetting("tunMode", {})
        kill_pref = settings.getSetting("killSwitch", {})
        return web.json_response(
            {
                "success": True,
                "connection": connection,
                "config": config_summary(config_result.get("config")),
                "tun": {
                    "enabled": bool(tun_pref.get("enabled", False)),
                    "hasPrivileges": bool(tun_pref.get("hasPrivileges", False)),
                },
                "killSwitch": {
                    "enabled": bool(kill_pref.get("enabled", False)),
                    "isActive": bool(kill_pref.get("isActive", False)),
                },
            }
        )

    async def api_connection(request: web.Request) -> web.Response:
        denied = _guard(request)
        if denied is not None:
            return denied
        body = await _body_json(request)
        if body is None or not isinstance(body.get("enable"), bool):
            return web.json_response(
                {"success": False, "error": "Expected JSON body {\"enable\": bool}"},
                status=400,
            )
        result = await handlers["toggle_connection"](body["enable"])
        status = 200 if result.get("success", False) else 502
        return web.json_response(result, status=status)

    async def api_tun(request: web.Request) -> web.Response:
        denied = _guard(request)
        if denied is not None:
            return denied
        body = await _body_json(request)
        if body is None or not isinstance(body.get("enabled"), bool):
            return web.json_response(
                {"success": False, "error": "Expected JSON body {\"enabled\": bool}"},
                status=400,
            )
        result = await handlers["toggle_tun_mode"](body["enabled"])
        status = 200 if result.get("success", False) else 502
        return web.json_response(result, status=status)

    async def api_killswitch(request: web.Request) -> web.Response:
        denied = _guard(request)
        if denied is not None:
            return denied
        body = await _body_json(request)
        if body is None or not isinstance(body.get("enabled"), bool):
            return web.json_response(
                {"success": False, "error": "Expected JSON body {\"enabled\": bool}"},
                status=400,
            )
        result = await handlers["toggle_kill_switch"](body["enabled"])
        status = 200 if result.get("success", False) else 502
        return web.json_response(result, status=status)

    async def api_killswitch_deactivate(request: web.Request) -> web.Response:
        denied = _guard(request)
        if denied is not None:
            return denied
        result = await handlers["deactivate_kill_switch"]()
        status = 200 if result.get("success", False) else 502
        return web.json_response(result, status=status)

    async def api_profiles(request: web.Request) -> web.Response:
        denied = _guard(request)
        if denied is not None:
            return denied
        result = await handlers["get_profiles"]()
        profiles = [
            config_summary(p) for p in result.get("profiles", []) if isinstance(p, dict)
        ]
        return web.json_response(
            {
                "success": bool(result.get("success", False)),
                "activeId": result.get("activeId"),
                "profiles": profiles,
                "subscription": result.get("subscription"),
            }
        )

    async def _profile_id_action(
        request: web.Request, handler_name: str
    ) -> web.Response:
        denied = _guard(request)
        if denied is not None:
            return denied
        body = await _body_json(request)
        profile_id = (body or {}).get("id")
        if not profile_id or not isinstance(profile_id, str):
            return web.json_response(
                {"success": False, "error": "Expected JSON body {\"id\": str}"},
                status=400,
            )
        result = await handlers[handler_name](profile_id)
        status = 200 if result.get("success", False) else 400
        return web.json_response(result, status=status)

    async def api_profile_activate(request: web.Request) -> web.Response:
        return await _profile_id_action(request, "set_active_profile")

    async def api_profile_remove(request: web.Request) -> web.Response:
        return await _profile_id_action(request, "remove_profile")

    async def api_profiles_ping(request: web.Request) -> web.Response:
        denied = _guard(request)
        if denied is not None:
            return denied
        result = await handlers["test_profiles_latency"]()
        status = 200 if result.get("success", False) else 502
        return web.json_response(result, status=status)

    async def api_subscription_refresh(request: web.Request) -> web.Response:
        denied = _guard(request)
        if denied is not None:
            return denied
        result = await handlers["refresh_subscription"]()
        status = 200 if result.get("success", False) else 502
        return web.json_response(result, status=status)

    async def api_subscription_rename(request: web.Request) -> web.Response:
        denied = _guard(request)
        if denied is not None:
            return denied
        body = await _body_json(request)
        name = (body or {}).get("name")
        if not isinstance(name, str) or not name.strip():
            return web.json_response(
                {"success": False, "error": "Expected JSON body {\"name\": str}"},
                status=400,
            )
        result = await handlers["rename_subscription"](name.strip())
        status = 200 if result.get("success", False) else 400
        return web.json_response(result, status=status)

    async def api_subscription_interval(request: web.Request) -> web.Response:
        denied = _guard(request)
        if denied is not None:
            return denied
        body = await _body_json(request)
        hours = (body or {}).get("hours")
        if not isinstance(hours, int) or isinstance(hours, bool) or hours < 0:
            return web.json_response(
                {"success": False, "error": "Expected JSON body {\"hours\": int>=0}"},
                status=400,
            )
        result = await handlers["set_subscription_refresh_interval"](hours)
        status = 200 if result.get("success", False) else 400
        return web.json_response(result, status=status)

    async def api_stats(request: web.Request) -> web.Response:
        denied = _guard(request)
        if denied is not None:
            return denied
        result = await handlers["get_traffic_stats"]()
        status = 200 if result.get("success", False) else 502
        return web.json_response(result, status=status)

    async def api_updates(request: web.Request) -> web.Response:
        denied = _guard(request)
        if denied is not None:
            return denied
        result = await handlers["check_updates"]()
        status = 200 if result.get("success", False) else 502
        return web.json_response(result, status=status)

    async def api_export(request: web.Request) -> web.Response:
        # Deliberately un-redacted: an export *is* the credentials. Gated by the
        # same token as every other endpoint, and only produced on this explicit
        # request (the panel reveals it behind a button, never in the list view).
        denied = _guard(request)
        if denied is not None:
            return denied
        result = await handlers["export_profiles"]()
        status = 200 if result.get("success", False) else 502
        return web.json_response(result, status=status)

    async def api_import(request: web.Request) -> web.Response:
        denied = _guard(request)
        if denied is not None:
            return denied
        body = await _body_json(request)
        link = (body or {}).get("link")
        if not link or not isinstance(link, str) or not link.strip():
            return web.json_response(
                {"success": False, "error": "Expected JSON body {\"link\": str}"},
                status=400,
            )
        result = await handlers["import_config"](link.strip())
        status = 200 if result.get("success", False) else 400
        return web.json_response(result, status=status)

    app.router.add_get("/admin", get_admin_page)
    if static_dir.is_dir():
        app.router.add_routes([web.static("/admin/static", str(static_dir))])
    app.router.add_get("/api/v1/status", api_status)
    app.router.add_post("/api/v1/connection", api_connection)
    app.router.add_post("/api/v1/tun", api_tun)
    app.router.add_post("/api/v1/killswitch", api_killswitch)
    app.router.add_post("/api/v1/killswitch/deactivate", api_killswitch_deactivate)
    app.router.add_post("/api/v1/import", api_import)
    app.router.add_get("/api/v1/profiles", api_profiles)
    app.router.add_post("/api/v1/profiles/activate", api_profile_activate)
    app.router.add_post("/api/v1/profiles/remove", api_profile_remove)
    app.router.add_post("/api/v1/profiles/ping", api_profiles_ping)
    app.router.add_post("/api/v1/subscription/refresh", api_subscription_refresh)
    app.router.add_post("/api/v1/subscription/rename", api_subscription_rename)
    app.router.add_post("/api/v1/subscription/interval", api_subscription_interval)
    app.router.add_get("/api/v1/stats", api_stats)
    app.router.add_get("/api/v1/updates", api_updates)
    app.router.add_get("/api/v1/export", api_export)
