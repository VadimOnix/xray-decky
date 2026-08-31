"""Tests for backend.src.singbox_import (sing-box JSON config import)."""

import asyncio
import json

from backend.src import importer
from backend.src.profile_store import ProfileStore
from backend.src.singbox_import import (
    looks_like_singbox_config,
    parse_singbox_config,
)


UUID = "a5a075d3-b3d5-4a03-b2e0-8a1f04b1cf75"


class _FakeSettings:
    def __init__(self):
        self.data = {}

    def getSetting(self, key, default=None):
        return self.data.get(key, default)

    def setSetting(self, key, value):
        self.data[key] = value

    def commit(self):
        pass


def _by_address(profiles):
    return {p["address"]: p for p in profiles}


# --- looks_like_singbox_config ---


def test_looks_like_singbox_config():
    assert looks_like_singbox_config('{"outbounds": []}')
    assert looks_like_singbox_config("  [ ]  ")
    assert not looks_like_singbox_config("vless://x@h:443")
    assert not looks_like_singbox_config("")
    assert not looks_like_singbox_config(None)


# --- parse_singbox_config ---


def test_full_config_imports_servers_and_skips_structural():
    config = {
        "outbounds": [
            {"type": "direct", "tag": "direct"},
            {"type": "block", "tag": "block"},
            {"type": "selector", "tag": "select", "outbounds": ["a", "b"]},
            {
                "type": "vless",
                "tag": "vless-server",
                "server": "v.example.com",
                "server_port": 443,
                "uuid": UUID,
                "flow": "xtls-rprx-vision",
                "tls": {"enabled": True, "server_name": "v.example.com"},
            },
            {
                "type": "trojan",
                "tag": "trojan-server",
                "server": "t.example.com",
                "server_port": 443,
                "password": "trojan-pw",
                "tls": {"enabled": True},
            },
            {
                "type": "shadowsocks",
                "tag": "ss-server",
                "server": "s.example.com",
                "server_port": 8388,
                "method": "aes-256-gcm",
                "password": "ss-pw",
            },
        ]
    }
    profiles = parse_singbox_config(json.dumps(config))
    by_addr = _by_address(profiles)
    assert set(by_addr) == {"v.example.com", "t.example.com", "s.example.com"}

    vless = by_addr["v.example.com"]
    assert vless["protocol"] == "vless"
    assert vless["uuid"] == UUID
    assert vless["flow"] == "xtls-rprx-vision"
    assert vless["core"] == "xray"

    ss = by_addr["s.example.com"]
    assert ss["protocol"] == "shadowsocks"
    assert ss["method"] == "aes-256-gcm"
    assert ss["password"] == "ss-pw"


def test_bare_outbounds_array():
    outbounds = [
        {
            "type": "trojan",
            "tag": "t",
            "server": "t.example.com",
            "server_port": 443,
            "password": "pw",
            "tls": {"enabled": True},
        }
    ]
    profiles = parse_singbox_config(json.dumps(outbounds))
    assert len(profiles) == 1
    assert profiles[0]["address"] == "t.example.com"


def test_vless_reality_and_ws_transport_preserved():
    config = {
        "outbounds": [
            {
                "type": "vless",
                "tag": "reality",
                "server": "r.example.com",
                "server_port": 443,
                "uuid": UUID,
                "transport": {
                    "type": "ws",
                    "path": "/vpn",
                    "headers": {"Host": "cdn.example.com"},
                },
                "tls": {
                    "enabled": True,
                    "server_name": "r.example.com",
                    "utls": {"fingerprint": "chrome"},
                    "reality": {
                        "enabled": True,
                        "public_key": "PUBKEY123",
                        "short_id": "ab12",
                    },
                },
            }
        ]
    }
    profile = parse_singbox_config(json.dumps(config))[0]
    assert profile["security"] == "reality"
    assert profile["network"] == "ws"
    assert profile["transport"]["path"] == "/vpn"
    assert profile["transport"]["host"] == "cdn.example.com"
    assert profile["realityConfig"]["publicKey"] == "PUBKEY123"
    assert profile["realityConfig"]["shortId"] == "ab12"


def test_vmess_roundtrips_through_share_link():
    config = {
        "outbounds": [
            {
                "type": "vmess",
                "tag": "vm",
                "server": "m.example.com",
                "server_port": 443,
                "uuid": UUID,
                "alter_id": 0,
                "security": "auto",
                "tls": {"enabled": True, "server_name": "m.example.com"},
            }
        ]
    }
    profile = parse_singbox_config(json.dumps(config))[0]
    assert profile["protocol"] == "vmess"
    assert profile["uuid"] == UUID
    assert profile["security"] == "tls"


def test_hysteria2_and_tuic_map_to_singbox_core():
    config = {
        "outbounds": [
            {
                "type": "hysteria2",
                "tag": "hy2",
                "server": "h.example.com",
                "server_port": 443,
                "password": "hy2-pw",
                "obfs": {"type": "salamander", "password": "obfs-pw"},
                "tls": {"enabled": True, "server_name": "h.example.com"},
            },
            {
                "type": "tuic",
                "tag": "tuic",
                "server": "u.example.com",
                "server_port": 443,
                "uuid": UUID,
                "password": "tuic-pw",
                "congestion_control": "bbr",
                "tls": {"enabled": True},
            },
        ]
    }
    by_addr = _by_address(parse_singbox_config(json.dumps(config)))
    hy2 = by_addr["h.example.com"]
    assert hy2["protocol"] == "hysteria2"
    # Backward-compat: sing-box JSON config used to mean "sing-box core";
    # since v26.7.28 hysteria2 runs on xray-core, so the importer maps it
    # there regardless. TUIC still uses sing-box.
    assert hy2["core"] == "xray-core"
    assert hy2["obfs"] == "salamander"
    tuic = by_addr["u.example.com"]
    assert tuic["protocol"] == "tuic"
    assert tuic["core"] == "sing-box"
    assert tuic["congestionControl"] == "bbr"


def test_incomplete_outbounds_are_skipped():
    config = {
        "outbounds": [
            {"type": "vless", "tag": "no-server", "uuid": UUID, "server_port": 443},
            {"type": "trojan", "tag": "no-pw", "server": "t.example.com",
             "server_port": 443},
            {"type": "unknownproto", "server": "x.example.com", "server_port": 1},
        ]
    }
    assert parse_singbox_config(json.dumps(config)) == []


def test_invalid_and_non_json_input():
    assert parse_singbox_config("{ not valid json") == []
    assert parse_singbox_config("vless://x@h:443") == []
    assert parse_singbox_config("") == []
    assert parse_singbox_config('{"outbounds": "wrong-type"}') == []


# --- integration through importer.import_link ---


def test_import_singbox_config_stores_all_servers():
    store = ProfileStore(_FakeSettings())
    config = {
        "outbounds": [
            {"type": "vless", "tag": "a", "server": "a.example.com",
             "server_port": 443, "uuid": UUID,
             "tls": {"enabled": True}},
            {"type": "trojan", "tag": "b", "server": "b.example.com",
             "server_port": 443, "password": "pw", "tls": {"enabled": True}},
        ]
    }
    result = asyncio.run(importer.import_link(store, json.dumps(config)))
    assert result["success"] is True
    assert result["profileCount"] == 2
    addresses = {p["address"] for p in store.list_profiles()}
    assert addresses == {"a.example.com", "b.example.com"}
    # A pasted config is not a refreshable subscription.
    assert store.get_subscription() is None


def test_import_singbox_config_without_servers_fails():
    store = ProfileStore(_FakeSettings())
    result = asyncio.run(
        importer.import_link(store, '{"outbounds": [{"type": "direct"}]}')
    )
    assert result["success"] is False
    assert "sing-box" in result["error"].lower()
    assert store.list_profiles() == []
