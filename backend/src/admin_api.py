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
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict

from aiohttp import web


Handler = Callable[..., Awaitable[Dict[str, Any]]]

# Profile fields safe to show in the panel (never credentials).
_SUMMARY_FIELDS = (
    "id",
    "protocol",
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
            remove_profile, test_profiles_latency, refresh_subscription.
        token: The admin token (see ensure_admin_token).
    """

    def _authorized(request: web.Request) -> bool:
        presented = request.headers.get("X-Admin-Token") or request.query.get(
            "token", ""
        )
        return bool(presented) and secrets.compare_digest(presented, token)

    def _unauthorized() -> web.Response:
        return web.json_response(
            {"success": False, "error": "Invalid or missing admin token"},
            status=401,
        )

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
        if not _authorized(request):
            return _unauthorized()
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
        if not _authorized(request):
            return _unauthorized()
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
        if not _authorized(request):
            return _unauthorized()
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
        if not _authorized(request):
            return _unauthorized()
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
        if not _authorized(request):
            return _unauthorized()
        result = await handlers["deactivate_kill_switch"]()
        status = 200 if result.get("success", False) else 502
        return web.json_response(result, status=status)

    async def api_profiles(request: web.Request) -> web.Response:
        if not _authorized(request):
            return _unauthorized()
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
        if not _authorized(request):
            return _unauthorized()
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
        if not _authorized(request):
            return _unauthorized()
        result = await handlers["test_profiles_latency"]()
        status = 200 if result.get("success", False) else 502
        return web.json_response(result, status=status)

    async def api_subscription_refresh(request: web.Request) -> web.Response:
        if not _authorized(request):
            return _unauthorized()
        result = await handlers["refresh_subscription"]()
        status = 200 if result.get("success", False) else 502
        return web.json_response(result, status=status)

    async def api_import(request: web.Request) -> web.Response:
        if not _authorized(request):
            return _unauthorized()
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
