"""Tests for backend.src.exporter (profile -> share link, round-trip stable)."""

import base64
import json

from backend.src.config_parser import parse_share_link, parse_subscription_content
from backend.src.exporter import export_profiles, profile_to_share_link


UUID = "a5a075d3-b3d5-4a03-b2e0-8a1f04b1cf75"


def _roundtrip(link: str) -> None:
    """parse(link) -> export -> parse must reproduce the same profile."""
    p1 = parse_share_link(link)
    assert p1 is not None, link
    exported = profile_to_share_link(p1)
    assert exported is not None, link
    p2 = parse_share_link(exported)
    assert p2 == p1, f"round-trip drift for {link}\n{p1}\n!=\n{p2}"


def test_roundtrip_vless_reality_tcp_vision():
    _roundtrip(
        f"vless://{UUID}@r.example.com:443?type=tcp&security=reality"
        f"&flow=xtls-rprx-vision&pbk=PUBKEY&sid=ab12&sni=example.com&fp=chrome&spx=%2F"
        "#Reality%20Node"
    )


def test_roundtrip_vless_tls_ws():
    _roundtrip(
        f"vless://{UUID}@w.example.com:443?type=ws&security=tls"
        "&path=%2Fws&host=cdn.example.com&sni=w.example.com&alpn=h2,http%2F1.1"
        "&fp=chrome#WS%20Node"
    )


def test_roundtrip_vless_grpc():
    _roundtrip(
        f"vless://{UUID}@g.example.com:443?type=grpc&security=tls"
        "&serviceName=mygrpc&sni=g.example.com"
    )


def test_roundtrip_trojan_grpc():
    _roundtrip(
        "trojan://s3cr3t@t.example.com:443?type=grpc&security=tls&serviceName=svc"
        "&sni=t.example.com#Trojan"
    )


def test_roundtrip_shadowsocks():
    _roundtrip("ss://aes-256-gcm:sspassword@s.example.com:8388#SS%20Node")


def test_roundtrip_socks_with_credentials():
    _roundtrip("socks://alice:s3cr3t@192.168.1.5:1080#Phone%20Hotspot")


def test_roundtrip_socks_without_credentials():
    _roundtrip("socks://192.168.1.5:1080#LAN")


def test_roundtrip_socks_username_only():
    _roundtrip("socks://alice@192.168.1.5:1080")


def test_roundtrip_vmess_ws_tls():
    vmess = {
        "v": "2",
        "ps": "VMess Node",
        "add": "m.example.com",
        "port": "443",
        "id": UUID,
        "aid": "0",
        "scy": "auto",
        "net": "ws",
        "type": "none",
        "host": "cdn.example.com",
        "path": "/vm",
        "tls": "tls",
        "sni": "m.example.com",
    }
    link = "vmess://" + base64.b64encode(json.dumps(vmess).encode()).decode()
    _roundtrip(link)


def test_roundtrip_hysteria2():
    _roundtrip(
        "hysteria2://hy2pw@h.example.com:443?sni=h.example.com&insecure=1"
        "&obfs=salamander&obfs-password=obfspw#Hy2"
    )


def test_roundtrip_hysteria2_xray_options():
    _roundtrip(
        "hysteria2://hy2pw@h.example.com"
        "?sni=h.example.com&alpn=h3&insecure=1"
        "&pinSHA256=" + "AA" * 32
        + "&mport=21000-22000&hop_interval=15"
        "&obfs=salamander&obfs-password=obfspw#Hy2"
    )


def test_roundtrip_tuic():
    _roundtrip(
        f"tuic://{UUID}:tuicpw@u.example.com:443?congestion_control=bbr"
        "&udp_relay_mode=native&sni=u.example.com&alpn=h3#TUIC"
    )


def test_unsupported_profile_returns_none():
    assert profile_to_share_link({"protocol": "wireguard"}) is None
    assert profile_to_share_link({}) is None
    assert profile_to_share_link("not-a-dict") is None
    # Missing endpoint / credentials.
    assert profile_to_share_link({"protocol": "vless", "uuid": UUID}) is None
    assert profile_to_share_link(
        {"protocol": "trojan", "address": "h", "port": 443}
    ) is None


def test_export_profiles_builds_links_and_subscription():
    profiles = [
        parse_share_link(f"vless://{UUID}@a.example.com:443?security=tls&sni=a"),
        parse_share_link("trojan://pw@b.example.com:443?sni=b"),
        {"protocol": "wireguard", "address": "skip.example.com"},  # unsupported
    ]
    result = export_profiles(profiles)
    assert result["count"] == 2
    assert len(result["links"]) == 2
    assert result["links"][0]["protocol"] == "vless"

    # The base64 subscription blob re-parses to the same two servers.
    decoded = base64.b64decode(result["subscription"]).decode()
    reparsed = parse_subscription_content(decoded)
    addresses = {p["address"] for p in reparsed}
    assert addresses == {"a.example.com", "b.example.com"}


def test_export_empty_list():
    result = export_profiles([])
    assert result == {"links": [], "subscription": "", "count": 0}
