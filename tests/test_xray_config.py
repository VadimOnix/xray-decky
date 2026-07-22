"""Tests for XrayManager._build_xray_config (xray-core config generation)."""

import pytest

from backend.src.xray_manager import XrayManager


UUID = "a5a075d3-b3d5-4a03-b2e0-8a1f04b1cf75"


def _build(profile, tun_mode=False, outbound_interface=None):
    return XrayManager()._build_xray_config(profile, tun_mode, outbound_interface)


def _proxy_outbound(config):
    return next(o for o in config["outbounds"] if o.get("tag") == "proxy")


def test_vless_reality_outbound():
    config = _build(
        {
            "protocol": "vless",
            "uuid": UUID,
            "address": "1.2.3.4",
            "port": 443,
            "flow": "xtls-rprx-vision",
            "network": "tcp",
            "security": "reality",
            "realityConfig": {
                "publicKey": "PUB",
                "shortId": "ab",
                "serverName": "example.com",
                "fingerprint": "chrome",
                "spiderX": "/",
            },
        }
    )
    outbound = _proxy_outbound(config)
    assert outbound["protocol"] == "vless"
    user = outbound["settings"]["vnext"][0]["users"][0]
    assert user == {"id": UUID, "encryption": "none", "flow": "xtls-rprx-vision"}
    reality = outbound["streamSettings"]["realitySettings"]
    assert reality["publicKey"] == "PUB"
    assert reality["spiderX"] == "/"
    # Client config must never contain server-side REALITY keys.
    assert "privateKey" not in reality
    assert "dest" not in reality


def test_legacy_profile_without_protocol_defaults_to_vless():
    config = _build(
        {"uuid": UUID, "address": "example.com", "port": 443, "security": "none"}
    )
    outbound = _proxy_outbound(config)
    assert outbound["protocol"] == "vless"
    assert outbound["streamSettings"]["network"] == "tcp"


def test_vless_ws_honors_path_and_host():
    config = _build(
        {
            "protocol": "vless",
            "uuid": UUID,
            "address": "example.com",
            "port": 443,
            "network": "ws",
            "security": "tls",
            "transport": {"path": "/ws", "host": "cdn.example.com"},
            "tlsConfig": {"serverName": "cdn.example.com", "alpn": ["h2"]},
        }
    )
    stream = _proxy_outbound(config)["streamSettings"]
    assert stream["wsSettings"] == {"path": "/ws", "host": "cdn.example.com"}
    assert stream["tlsSettings"]["serverName"] == "cdn.example.com"
    assert stream["tlsSettings"]["alpn"] == ["h2"]
    assert "allowInsecure" not in stream["tlsSettings"]


def test_tls_server_name_falls_back_to_transport_host_then_address():
    profile = {
        "protocol": "vless",
        "uuid": UUID,
        "address": "1.2.3.4",
        "port": 443,
        "network": "ws",
        "security": "tls",
        "transport": {"host": "cdn.example.com"},
    }
    stream = _proxy_outbound(_build(profile))["streamSettings"]
    assert stream["tlsSettings"]["serverName"] == "cdn.example.com"

    profile.pop("transport")
    stream = _proxy_outbound(_build(profile))["streamSettings"]
    assert stream["tlsSettings"]["serverName"] == "1.2.3.4"


def test_grpc_httpupgrade_xhttp_kcp_settings():
    base = {"protocol": "vless", "uuid": UUID, "address": "h.io", "port": 443}

    grpc = _proxy_outbound(
        _build(
            {
                **base,
                "network": "grpc",
                "transport": {"serviceName": "svc", "multiMode": True},
            }
        )
    )["streamSettings"]
    assert grpc["grpcSettings"] == {"serviceName": "svc", "multiMode": True}

    hu = _proxy_outbound(
        _build({**base, "network": "httpupgrade", "transport": {"path": "/up"}})
    )["streamSettings"]
    assert hu["httpupgradeSettings"] == {"path": "/up"}

    xh = _proxy_outbound(
        _build(
            {
                **base,
                "network": "xhttp",
                "transport": {"path": "/xh", "mode": "packet-up"},
            }
        )
    )["streamSettings"]
    assert xh["xhttpSettings"] == {"path": "/xh", "mode": "packet-up"}

    kcp = _proxy_outbound(
        _build(
            {
                **base,
                "network": "kcp",
                "transport": {"headerType": "dtls", "seed": "s"},
            }
        )
    )["streamSettings"]
    assert kcp["kcpSettings"] == {"header": {"type": "dtls"}, "seed": "s"}


def test_vmess_outbound():
    config = _build(
        {
            "protocol": "vmess",
            "uuid": UUID,
            "address": "example.com",
            "port": 443,
            "network": "ws",
            "security": "tls",
            "alterId": 0,
            "vmessSecurity": "aes-128-gcm",
            "transport": {"path": "/vm"},
        }
    )
    outbound = _proxy_outbound(config)
    assert outbound["protocol"] == "vmess"
    user = outbound["settings"]["vnext"][0]["users"][0]
    assert user == {"id": UUID, "alterId": 0, "security": "aes-128-gcm"}


def test_trojan_outbound():
    config = _build(
        {
            "protocol": "trojan",
            "password": "p@ss",
            "address": "example.com",
            "port": 443,
            "network": "tcp",
            "security": "tls",
        }
    )
    outbound = _proxy_outbound(config)
    assert outbound["protocol"] == "trojan"
    assert outbound["settings"]["servers"] == [
        {"address": "example.com", "port": 443, "password": "p@ss"}
    ]
    assert outbound["streamSettings"]["tlsSettings"]["serverName"] == "example.com"


def test_shadowsocks_outbound():
    config = _build(
        {
            "protocol": "shadowsocks",
            "method": "aes-256-gcm",
            "password": "pw",
            "address": "1.2.3.4",
            "port": 8388,
            "network": "tcp",
            "security": "none",
        }
    )
    outbound = _proxy_outbound(config)
    assert outbound["protocol"] == "shadowsocks"
    assert outbound["settings"]["servers"] == [
        {"address": "1.2.3.4", "port": 8388, "method": "aes-256-gcm", "password": "pw"}
    ]


def test_unsupported_protocol_raises():
    with pytest.raises(ValueError):
        _build({"protocol": "hysteria2", "address": "h.io", "port": 443})


def test_sniffing_and_private_bypass_always_present():
    config = _build(
        {"protocol": "vless", "uuid": UUID, "address": "h.io", "port": 443}
    )
    for inbound in config["inbounds"]:
        if inbound["tag"] == "api":
            continue
        assert inbound["sniffing"]["enabled"] is True
        assert "quic" in inbound["sniffing"]["destOverride"]
    tags = [o["tag"] for o in config["outbounds"]]
    assert tags == ["proxy", "direct"]
    rules = config["routing"]["rules"]
    # The API rule must come before the private-IP bypass (its destination
    # is 127.0.0.1), which must come before everything else.
    assert rules[0] == {"type": "field", "inboundTag": ["api"], "outboundTag": "api"}
    assert rules[1]["ip"] == ["geoip:private"]
    assert rules[1]["outboundTag"] == "direct"


def test_stats_service_enabled():
    config = _build(
        {"protocol": "vless", "uuid": UUID, "address": "h.io", "port": 443}
    )
    assert config["stats"] == {}
    assert config["policy"]["system"]["statsOutboundUplink"] is True
    assert config["policy"]["system"]["statsOutboundDownlink"] is True
    assert config["api"] == {"tag": "api", "services": ["StatsService"]}
    api_inbound = next(i for i in config["inbounds"] if i["tag"] == "api")
    assert api_inbound["listen"] == "127.0.0.1"
    assert api_inbound["protocol"] == "dokodemo-door"


def test_tun_mode_adds_inbound_rule_and_sockopt():
    config = _build(
        {"protocol": "vless", "uuid": UUID, "address": "h.io", "port": 443},
        tun_mode=True,
        outbound_interface="wlan0",
    )
    protocols = [i["protocol"] for i in config["inbounds"]]
    assert "tun" in protocols
    tun_rules = [
        r for r in config["routing"]["rules"] if r.get("inboundTag") == ["tun"]
    ]
    assert tun_rules and tun_rules[0]["outboundTag"] == "proxy"
    stream = _proxy_outbound(config)["streamSettings"]
    assert stream["sockopt"] == {"interface": "wlan0"}


def test_tun_rule_comes_after_private_bypass():
    """
    Rules are first-match. The TUN catch-all must sit BEHIND the
    private-IP bypass, or LAN traffic and DNS queries to the home router
    get sent into the tunnel and die — no internet while connected
    (the v1 TUN bug that came back with the stats API rule).
    """
    config = _build(
        {"protocol": "vless", "uuid": UUID, "address": "h.io", "port": 443},
        tun_mode=True,
        outbound_interface="wlan0",
    )
    rules = config["routing"]["rules"]
    private_idx = next(
        i for i, r in enumerate(rules) if r.get("ip") == ["geoip:private"]
    )
    tun_idx = next(
        i for i, r in enumerate(rules) if r.get("inboundTag") == ["tun"]
    )
    assert private_idx < tun_idx


def test_no_tun_inbound_without_tun_mode():
    config = _build(
        {"protocol": "vless", "uuid": UUID, "address": "h.io", "port": 443}
    )
    assert all(i["protocol"] != "tun" for i in config["inbounds"])
