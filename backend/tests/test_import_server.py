"""Tests for backend.src.import_server (web import endpoint)."""

import asyncio
from pathlib import Path

from aiohttp.test_utils import TestClient, TestServer

from backend.src.admin_api import ensure_admin_token
from backend.src.import_server import create_import_app

UUID = "a5a075d3-b3d5-4a03-b2e0-8a1f04b1cf75"
LINK = f"vless://{UUID}@a.example.com:443?security=tls"
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


class _FakeSettings:
    def __init__(self):
        self.data = {}

    def getSetting(self, key, default=None):
        return self.data.get(key, default)

    def setSetting(self, key, value):
        self.data[key] = value

    def commit(self):
        pass


def _post_import(settings, link):
    async def run():
        app = create_import_app(settings, STATIC_DIR)
        async with TestClient(TestServer(app)) as client:
            resp = await client.post("/import", data={"link": link})
            return resp.status, await resp.json()

    return asyncio.run(run())


def test_first_import_returns_admin_url():
    settings = _FakeSettings()
    status, data = _post_import(settings, LINK)
    assert status == 200
    assert data["success"] is True
    # Bootstrap pairing: the very first import hands out the panel URL
    # with the same token the QAM's QR code embeds.
    assert data["adminUrl"] == f"/admin?token={ensure_admin_token(settings)}"


def test_second_import_omits_admin_url():
    settings = _FakeSettings()
    _post_import(settings, LINK)
    status, data = _post_import(settings, "trojan://pw@b.example.com:443")
    assert status == 200
    assert data["success"] is True
    assert "adminUrl" not in data


def test_invalid_link_gets_400_and_no_admin_url():
    settings = _FakeSettings()
    status, data = _post_import(settings, "not-a-link")
    assert status == 400
    assert data["success"] is False
    assert "adminUrl" not in data
