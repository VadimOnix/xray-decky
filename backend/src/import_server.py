"""
Import HTTP server for proxy share-link import via web form.

Serves GET /import (HTML form), GET /import/static/* (CSS/JS),
POST /import (validate and store the share link).
Contract: specs/002-vless-import-qr/contracts/import-http-api.md
"""

from pathlib import Path
from typing import Awaitable, Callable, Optional

from aiohttp import web

from .importer import import_link
from .profile_store import ProfileStore


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
        POST /import — accept a share link (form or JSON), validate, store in SettingsManager.
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

        try:
            result = await import_link(ProfileStore(settings), link)
            if not result.get("success", False):
                return web.json_response(
                    {
                        "success": False,
                        "error": result.get("error") or "Invalid share link format",
                    },
                    status=400,
                )

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
