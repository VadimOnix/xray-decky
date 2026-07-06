"""Tests for backend.src.importer (shared import flow + subscriptions)."""

import asyncio
import base64
from unittest.mock import patch

from backend.src import importer
from backend.src.config_parser import parse_subscription_content
from backend.src.profile_store import ProfileStore


UUID = "a5a075d3-b3d5-4a03-b2e0-8a1f04b1cf75"
LINK_A = f"vless://{UUID}@a.example.com:443?security=tls"
LINK_B = "trojan://pw@b.example.com:443"


class _FakeSettings:
    def __init__(self):
        self.data = {}

    def getSetting(self, key, default=None):
        return self.data.get(key, default)

    def setSetting(self, key, value):
        self.data[key] = value

    def commit(self):
        pass


def _b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


def _store() -> ProfileStore:
    return ProfileStore(_FakeSettings())


def _run(coro):
    return asyncio.run(coro)


def _patched_fetch(body, userinfo=None):
    async def fake_fetch(_url, timeout=importer.FETCH_TIMEOUT):
        return importer.SubscriptionResponse(body, userinfo)

    return patch.object(importer, "fetch_subscription", fake_fetch)


# --- parse_subscription_content ---


def test_content_base64_and_plaintext():
    payload = f"{LINK_A}\n{LINK_B}\n"
    assert len(parse_subscription_content(_b64(payload))) == 2
    assert len(parse_subscription_content(payload)) == 2
    assert parse_subscription_content("no links here") == []
    assert parse_subscription_content("") == []


# --- import_link ---


def test_import_single_link_appends():
    store = _store()
    result = _run(importer.import_link(store, LINK_A))
    assert result["success"] is True
    assert result["profileCount"] == 1

    result = _run(importer.import_link(store, LINK_B))
    assert result["profileCount"] == 2
    # Newest import becomes active.
    assert store.get_active()["protocol"] == "trojan"


def test_import_subscription_url_stores_all_and_meta():
    store = _store()
    with _patched_fetch(f"{LINK_A}\n{LINK_B}\n"):
        result = _run(importer.import_link(store, "https://sub.example.com/s"))
    assert result["success"] is True
    assert result["profileCount"] == 2
    subscription = store.get_subscription()
    assert subscription["url"] == "https://sub.example.com/s"
    assert subscription["nodeCount"] == 2
    assert subscription["name"] == "sub.example.com"  # derived from the URL host


def test_parse_subscription_userinfo():
    info = importer.parse_subscription_userinfo(
        "upload=100; download=200; total=1000; expire=1719705600"
    )
    assert info == {
        "upload": 100,
        "download": 200,
        "total": 1000,
        "expire": 1719705600,
    }
    # Partial / messy input keeps what it can.
    assert importer.parse_subscription_userinfo("total=500; junk; download=x") == {
        "total": 500
    }
    assert importer.parse_subscription_userinfo("") is None
    assert importer.parse_subscription_userinfo(None) is None
    assert importer.parse_subscription_userinfo("nothing-here") is None


def test_import_subscription_stores_userinfo():
    store = _store()
    userinfo = {"upload": 1, "download": 2, "total": 1000, "expire": 1719705600}
    with _patched_fetch(f"{LINK_A}\n{LINK_B}\n", userinfo=userinfo):
        result = _run(importer.import_link(store, "https://sub.example.com/s"))
    assert result["success"] is True
    assert store.get_subscription()["userinfo"] == userinfo


def test_import_subscription_preserves_manual_profile():
    store = _store()
    # A manually added single server.
    _run(importer.import_link(store, LINK_A))
    manual_count = len(store.list_profiles())
    assert manual_count == 1

    # Importing a subscription must not wipe the manual server.
    with _patched_fetch("trojan://pw@s1.example.com:443\ntrojan://pw@s2.example.com:443\n"):
        result = _run(importer.import_link(store, "https://sub.example.com/s"))
    assert result["success"] is True
    addresses = {p["address"] for p in store.list_profiles()}
    # The manual server survives alongside the two new subscription servers.
    assert addresses == {"a.example.com", "s1.example.com", "s2.example.com"}


def test_import_subscription_url_fetch_failure():
    store = _store()
    with _patched_fetch(None):
        result = _run(importer.import_link(store, "https://sub.example.com/s"))
    assert result["success"] is False
    assert "fetch" in result["error"].lower()
    assert store.list_profiles() == []


def test_import_subscription_url_without_links():
    store = _store()
    with _patched_fetch("<html>not a subscription</html>"):
        result = _run(importer.import_link(store, "https://sub.example.com/s"))
    assert result["success"] is False


def test_import_pasted_base64_subscription():
    store = _store()
    result = _run(importer.import_link(store, _b64(f"{LINK_A}\n{LINK_B}")))
    assert result["success"] is True
    assert result["profileCount"] == 2
    # Pasted content is not a refreshable subscription.
    assert store.get_subscription() is None


def test_import_invalid_link():
    store = _store()
    result = _run(importer.import_link(store, "naive+https://x@h:443"))
    assert result["success"] is False
    result = _run(importer.import_link(store, "   "))
    assert result["success"] is False


def test_import_hysteria2_stores_singbox_profile():
    store = _store()
    result = _run(importer.import_link(store, "hysteria2://pw@h2.example.com:443"))
    assert result["success"] is True
    assert store.get_active()["core"] == "sing-box"


# --- refresh_subscription ---


def test_refresh_replaces_list_and_preserves_active():
    store = _store()
    with _patched_fetch(f"{LINK_A}\n{LINK_B}\n"):
        _run(importer.import_link(store, "https://sub.example.com/s"))

    # Make the second server active, then refresh with reversed order.
    second = next(
        p for p in store.list_profiles() if p["protocol"] == "trojan"
    )
    store.set_active(second["id"])

    with _patched_fetch(f"{LINK_B}\n{LINK_A}\n"):
        result = _run(importer.refresh_subscription(store))
    assert result["success"] is True
    # Active server survived the refresh (matched by protocol/address/port).
    active = store.get_active()
    assert active["protocol"] == "trojan"
    assert active["address"] == "b.example.com"


def test_refresh_without_subscription():
    store = _store()
    result = _run(importer.refresh_subscription(store))
    assert result["success"] is False
