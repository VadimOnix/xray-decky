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


# --- fetch_subscription fallback chain ---


def _failing_aiohttp(calls):
    async def fake(_url, _timeout, proxy=None):
        calls.append(proxy)
        raise OSError("stalled")

    return fake


def _no_bypass():
    """No TUN default route in place, so no tunnel-bypass attempt is offered."""

    async def fake():
        return None

    return patch.object(importer, "_tunnel_bypass_interface", fake)


def _bypass_via(interface):
    async def fake():
        return interface

    return patch.object(importer, "_tunnel_bypass_interface", fake)


def test_fetch_falls_back_to_proxy_then_curl():
    aiohttp_calls, curl_calls = [], []

    async def fake_curl(_url, _timeout, interface=None):
        curl_calls.append(interface)
        return importer.SubscriptionResponse(LINK_A, None)

    with _no_bypass():
        with patch.object(
            importer, "_fetch_via_aiohttp", _failing_aiohttp(aiohttp_calls)
        ):
            with patch.object(importer, "_fetch_via_curl", fake_curl):
                response = _run(
                    importer.fetch_subscription("https://sub.example.com/s")
                )

    assert response.body == LINK_A
    # Direct first, then through the local proxy, then curl.
    assert aiohttp_calls == [None, importer._LOCAL_HTTP_PROXY]
    assert curl_calls == [None]


def test_fetch_proxy_success_skips_curl():
    async def fake_aiohttp(_url, _timeout, proxy=None):
        if proxy is None:
            raise OSError("stalled")
        return importer.SubscriptionResponse(LINK_A, None)

    async def fake_curl(_url, _timeout, interface=None):
        raise AssertionError("curl must not run when the proxy path succeeds")

    with _no_bypass():
        with patch.object(importer, "_fetch_via_aiohttp", fake_aiohttp):
            with patch.object(importer, "_fetch_via_curl", fake_curl):
                response = _run(
                    importer.fetch_subscription("https://sub.example.com/s")
                )

    assert response.body == LINK_A


def test_fetch_all_attempts_failing_returns_none():
    async def fake_curl(_url, _timeout, interface=None):
        return importer.SubscriptionResponse(None, None)

    with _no_bypass():
        with patch.object(importer, "_fetch_via_aiohttp", _failing_aiohttp([])):
            with patch.object(importer, "_fetch_via_curl", fake_curl):
                response = _run(
                    importer.fetch_subscription("https://sub.example.com/s")
                )

    assert response.body is None


# --- tunnel bypass (TUN mode hijacks the default route) ---


def test_fetch_bypasses_tunnel_via_physical_interface():
    """
    With TUN mode up, ``default dev xray0 metric 100`` outranks the physical
    default, so the plain aiohttp GET and the plain curl GET both enter the
    tunnel and fail together. The interface-bound attempt is the only one that
    leaves the Deck over wlan0 — it must run, and run before the tunnel-only
    local-proxy attempt.
    """
    order, curl_calls = [], []

    async def fake_aiohttp(_url, _timeout, proxy=None):
        order.append(f"aiohttp:{proxy}")
        raise OSError("Network is unreachable")

    async def fake_curl(_url, _timeout, interface=None):
        order.append(f"curl:{interface}")
        curl_calls.append(interface)
        if interface == "wlan0":
            return importer.SubscriptionResponse(LINK_A, None)
        return importer.SubscriptionResponse(None, None)

    with _bypass_via("wlan0"):
        with patch.object(importer, "_fetch_via_aiohttp", fake_aiohttp):
            with patch.object(importer, "_fetch_via_curl", fake_curl):
                response = _run(
                    importer.fetch_subscription("https://sub.example.com/s")
                )

    assert response.body == LINK_A
    assert curl_calls == ["wlan0"]
    # Bypass is attempted right after the plain GET, before the proxy path.
    assert order == ["aiohttp:None", "curl:wlan0"]


def test_fetch_still_tries_tunnel_when_bypass_fails():
    """
    Mirror case: the subscription host is blocked by the ISP but reachable
    through the tunnel. The bypass must not short-circuit the proxy attempt.
    """

    async def fake_aiohttp(_url, _timeout, proxy=None):
        if proxy is None:
            raise OSError("blocked")
        return importer.SubscriptionResponse(LINK_B, None)

    async def fake_curl(_url, _timeout, interface=None):
        return importer.SubscriptionResponse(None, None)

    with _bypass_via("wlan0"):
        with patch.object(importer, "_fetch_via_aiohttp", fake_aiohttp):
            with patch.object(importer, "_fetch_via_curl", fake_curl):
                response = _run(
                    importer.fetch_subscription("https://sub.example.com/s")
                )

    assert response.body == LINK_B


def test_fetch_skips_bypass_attempt_when_no_tun_route():
    """Without a TUN default route the bypass would just duplicate 'direct'."""
    curl_calls = []

    async def fake_curl(_url, _timeout, interface=None):
        curl_calls.append(interface)
        return importer.SubscriptionResponse(None, None)

    with _no_bypass():
        with patch.object(importer, "_fetch_via_aiohttp", _failing_aiohttp([])):
            with patch.object(importer, "_fetch_via_curl", fake_curl):
                _run(importer.fetch_subscription("https://sub.example.com/s"))

    assert curl_calls == [None]


def test_bypass_detection_failure_does_not_break_fetch():
    async def exploding_bypass():
        raise OSError("ip: command not found")

    async def fake_aiohttp(_url, _timeout, proxy=None):
        return importer.SubscriptionResponse(LINK_A, None)

    with patch.object(importer, "_tunnel_bypass_interface", exploding_bypass):
        with patch.object(importer, "_fetch_via_aiohttp", fake_aiohttp):
            response = _run(importer.fetch_subscription("https://sub.example.com/s"))

    assert response.body == LINK_A


def test_curl_binds_to_interface_when_given():
    """The bypass relies on curl's --interface (SO_BINDTODEVICE on Linux)."""
    argv, _ = _run(_captured_curl_call(interface="wlan0"))
    assert "--interface" in argv
    assert argv[argv.index("--interface") + 1] == "wlan0"


def test_curl_omits_interface_flag_by_default():
    argv, _ = _run(_captured_curl_call(interface=None))
    assert "--interface" not in argv


def test_curl_pins_the_system_ca_bundle():
    """
    Without --cacert, curl uses whatever the sandbox's CA variables point at.
    """
    with patch.object(importer, "system_ca_bundle", lambda: "/etc/ssl/ca.pem"):
        argv, _ = _run(_captured_curl_call(interface=None))
    assert argv[argv.index("--cacert") + 1] == "/etc/ssl/ca.pem"


def test_curl_omits_cacert_when_no_bundle_is_found():
    with patch.object(importer, "system_ca_bundle", lambda: None):
        argv, _ = _run(_captured_curl_call(interface=None))
    assert "--cacert" not in argv


def test_curl_runs_with_a_scrubbed_environment():
    """
    Under the sandbox's LD_LIBRARY_PATH curl loads the bundle's older
    libssl.so.3 and dies before opening a socket.
    """
    dirty = {"PATH": "/usr/bin", "LD_LIBRARY_PATH": "/tmp/_MEIabc"}
    with patch.dict("os.environ", dirty, clear=True):
        _, kwargs = _run(_captured_curl_call(interface=None))
    env = kwargs.get("env")
    assert env is not None, "curl must not inherit the sandbox environment"
    assert "LD_LIBRARY_PATH" not in env
    assert env["PATH"] == "/usr/bin"


async def _captured_curl_call(interface):
    """Run _fetch_via_curl against a stubbed subprocess; return (argv, kwargs)."""
    seen = []
    seen_kwargs = {}

    class _Proc:
        returncode = 0

        async def communicate(self):
            return b"HTTP/1.1 200 OK\r\n\r\n" + LINK_A.encode(), b""

    async def fake_exec(*args, **kwargs):
        seen.extend(args)
        seen_kwargs.update(kwargs)
        return _Proc()

    with patch("shutil.which", lambda _name: "/usr/bin/curl"):
        with patch("asyncio.create_subprocess_exec", fake_exec):
            await importer._fetch_via_curl(
                "https://sub.example.com/s", 8.0, interface=interface
            )
    return list(seen), dict(seen_kwargs)


# --- capped body reads ---


class _ChunkedStream:
    """
    Stand-in for aiohttp's StreamReader: read(n) hands back at most one
    buffered chunk, so it returns fewer than n bytes even when more are coming.
    """

    def __init__(self, chunks):
        self._chunks = list(chunks)
        self.requested = []

    async def read(self, n):
        self.requested.append(n)
        if not self._chunks:
            return b""
        chunk = self._chunks.pop(0)
        if len(chunk) > n:
            self._chunks.insert(0, chunk[n:])
            chunk = chunk[:n]
        return chunk


def test_read_capped_joins_short_reads():
    stream = _ChunkedStream([b"vless://a", b"\ntrojan://b", b"\n"])
    body = _run(importer._read_capped(stream, 1024))
    assert body == b"vless://a\ntrojan://b\n"


def test_read_capped_accepts_body_exactly_at_the_limit():
    stream = _ChunkedStream([b"x" * 5, b"x" * 5])
    assert _run(importer._read_capped(stream, 10)) == b"x" * 10


def test_read_capped_stops_one_byte_past_the_limit():
    stream = _ChunkedStream([b"x" * 8, b"y" * 8, b"z" * 8])
    body = _run(importer._read_capped(stream, 10))
    # One byte past the cap: enough for the caller to reject an oversized body,
    # without draining a hostile server's stream.
    assert len(body) == 11
    assert stream._chunks  # stopped early rather than reading to EOF


def test_fetch_rejects_non_http_schemes():
    response = _run(importer.fetch_subscription("ftp://sub.example.com/s"))
    assert response == importer.SubscriptionResponse(None, None)


def test_split_curl_output_redirect_chain():
    raw = (
        b"HTTP/1.1 301 Moved Permanently\r\n"
        b"Location: https://sub.example.com/final\r\n"
        b"\r\n"
        b"HTTP/2 200\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"Subscription-Userinfo: upload=1; download=2; total=3; expire=4\r\n"
        b"\r\n"
        b"body-bytes"
    )
    status, headers, body = importer._split_curl_output(raw)
    assert status == 200
    assert headers["subscription-userinfo"] == "upload=1; download=2; total=3; expire=4"
    assert body == b"body-bytes"


def test_split_curl_output_plain_body_without_headers():
    status, headers, body = importer._split_curl_output(b"just-a-body")
    assert status is None
    assert headers == {}
    assert body == b"just-a-body"


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


def test_import_socks_stores_xray_profile():
    store = _store()
    result = _run(importer.import_link(store, "socks://user:pw@192.168.1.5:1080#Phone"))
    assert result["success"] is True
    active = store.get_active()
    assert active["protocol"] == "socks"
    assert active["core"] == "xray"
    assert active["configType"] == "single"


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
