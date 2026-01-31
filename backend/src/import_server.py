"""
Import HTTP server for VLESS link import via web form.

Serves GET /import (HTML form), GET /import/static/* (CSS/JS), POST /import (validate and store VLESS).
Contract: specs/002-vless-import-qr/contracts/import-http-api.md
"""

import time
from pathlib import Path
from typing import Awaitable, Callable, Optional

from aiohttp import web

from .config_parser import (
    validate_vless_url,
    parse_vless_url,
    parse_subscription_url,
    build_vless_config,
)


def create_import_app(
    settings,
    static_dir: Path,
    on_vless_saved: Optional[Callable[[], Awaitable[None]]] = None,
) -> web.Application:
    """Create aiohttp app for import page. static_dir: path to backend/static."""
    app = web.Application()

    async def get_import_page(_request: web.Request) -> web.StreamResponse:
        """GET /import — serve import page HTML. Same form when opened directly (no redirect or auth)."""
        html_path = static_dir / "import.html"
        if not html_path.is_file():
            return web.Response(status=404, text="import.html not found")
        return web.FileResponse(html_path, headers={"Content-Type": "text/html"})

    async def post_import(request: web.Request) -> web.Response:
        """
        POST /import — accept VLESS link (form or JSON), validate, store in SettingsManager.
        Returns 200 JSON on success; 400/500 with { success: false, error: "..." } on failure.
        Invalid or empty link: 400, no overwrite of vlessConfig.
        """
        link = None
        content_type = request.headers.get("Content-Type", "")

        if "application/json" in content_type:
            try:
                body = await request.json()
                link = (body or {}).get("link") or (body or {}).get("vless")
            except Exception:
                return web.json_response(
                    {"success": False, "error": "Invalid JSON body"},
                    status=400,
                )
        else:
            # form: application/x-www-form-urlencoded
            try:
                data = await request.post()
                link = data.get("link") or data.get("vless")
            except Exception:
                return web.json_response(
                    {"success": False, "error": "Invalid form body"},
                    status=400,
                )

        if not link or not isinstance(link, str):
            return web.json_response(
                {"success": False, "error": "Missing or invalid link"},
                status=400,
            )

        link = link.strip()
        if not link:
            return web.json_response(
                {"success": False, "error": "Empty link"},
                status=400,
            )

        is_valid, error_msg = validate_vless_url(link)
        if not is_valid:
            return web.json_response(
                {"success": False, "error": error_msg or "Invalid VLESS URL format"},
                status=400,
            )

        try:
            parsed = parse_vless_url(link)
            config_type = "single"
            if not parsed:
                parsed_configs = parse_subscription_url(link)
                if not parsed_configs:
                    return web.json_response(
                        {"success": False, "error": "Failed to parse VLESS URL"},
                        status=400,
                    )
                parsed = parsed_configs[0]
                config_type = "subscription"

            config = build_vless_config(parsed, link, config_type)
            config["lastValidatedAt"] = int(time.time())

            settings.setSetting("vlessConfig", config)
            settings.commit()

            if on_vless_saved is not None:
                await on_vless_saved()

            return web.json_response(
                {"success": True, "message": "Saved"},
                status=200,
            )
        except Exception as e:
            return web.json_response(
                {"success": False, "error": str(e)},
                status=500,
            )

    app.router.add_get("/import", get_import_page)
    app.router.add_post("/import", post_import)
    app.router.add_routes([web.static("/import/static", str(static_dir))])

    return app
