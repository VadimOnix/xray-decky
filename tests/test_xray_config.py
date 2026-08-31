"""Tests for XrayManager._build_xray_config (xray-core config generation)."""

import json
import os

import pytest

from backend.src.xray_manager import XrayManager


UUID = "a5a075d3-b3d5-4a03-b2e0-8a1f04b1cf75"


def _build(profile, tun_mode=False, outbound_interface=None, route_rules=None):
    return XrayManager()._build_xray_config(
        profile, tun_mode, outbound_interface, route_rules=route_rules
    )


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


def test_socks_outbound_with_credentials():
    config = _build(
        {
            "protocol": "socks",
            "username": "alice",
            "password": "pw",
            "address": "192.168.1.5",
            "port": 1080,
            "network": "tcp",
            "security": "none",
        }
    )
    outbound = _proxy_outbound(config)
    assert outbound["protocol"] == "socks"
    assert outbound["settings"]["servers"] == [
        {
            "address": "192.168.1.5",
            "port": 1080,
            "users": [{"user": "alice", "pass": "pw"}],
        }
    ]
    assert outbound["streamSettings"]["network"] == "tcp"
    assert outbound["streamSettings"]["security"] == "none"


def test_socks_outbound_without_credentials_omits_users():
    config = _build(
        {"protocol": "socks", "address": "192.168.1.5", "port": 1080}
    )
    server = _proxy_outbound(config)["settings"]["servers"][0]
    assert server == {"address": "192.168.1.5", "port": 1080}


def test_socks_outbound_never_negotiates_tls():
    # A stored profile claiming TLS must not produce tlsSettings: plain SOCKS5
    # has no transport security, and pretending otherwise would fail to dial.
    config = _build(
        {
            "protocol": "socks",
            "address": "192.168.1.5",
            "port": 1080,
            "security": "tls",
        }
    )
    stream = _proxy_outbound(config)["streamSettings"]
    assert stream["security"] == "none"
    assert "tlsSettings" not in stream


def test_unsupported_protocol_raises():
    # hysteria2 was added in v26.7.28 — pick a name that still isn't a protocol.
    with pytest.raises(ValueError):
        _build({"protocol": "mtproto", "address": "h.io", "port": 443})


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
        r
        for r in config["routing"]["rules"]
        if r.get("inboundTag") == ["tun"] and r.get("port") is None
    ]
    assert tun_rules and tun_rules[0]["outboundTag"] == "proxy"
    stream = _proxy_outbound(config)["streamSettings"]
    assert stream["sockopt"] == {"interface": "wlan0"}


def test_tun_inbound_names_the_interface_tun_manager_waits_for():
    config = _build(
        {"protocol": "vless", "uuid": UUID, "address": "h.io", "port": 443},
        tun_mode=True,
        outbound_interface="wlan0",
    )
    tun = next(inbound for inbound in config["inbounds"] if inbound["protocol"] == "tun")
    assert tun["settings"]["name"] == "xray0"


def test_tun_mode_binds_direct_outbound_to_physical_interface():
    config = _build(
        {"protocol": "vless", "uuid": UUID, "address": "h.io", "port": 443},
        tun_mode=True,
        outbound_interface="wlan0",
    )
    direct = next(outbound for outbound in config["outbounds"] if outbound["tag"] == "direct")
    assert direct["streamSettings"]["sockopt"] == {"interface": "wlan0"}


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
        i
        for i, r in enumerate(rules)
        if r.get("inboundTag") == ["tun"] and r.get("port") is None
    )
    assert private_idx < tun_idx


def test_tun_mode_hijacks_dns_and_preserves_direct_domain_rules():
    config = _build(
        {"protocol": "vless", "uuid": UUID, "address": "h.io", "port": 443},
        tun_mode=True,
        outbound_interface="wlan0",
        route_rules=[
            _rr(
                action="direct",
                match={"type": "geosite", "value": "geosite:steam@cn"},
            )
        ],
    )

    steam_rule = next(
        rule
        for rule in config["routing"]["rules"]
        if rule.get("domain") and "geosite:steam@cn" in rule["domain"]
    )
    assert {
        "domain:steamcontent.com",
        "domain:steampipe.akamaized.net",
        "domain:steamcdn-a.akamaihd.net",
    }.issubset(steam_rule["domain"])
    assert config["dns"] == {
        "servers": [
            {"address": "fakedns", "domains": steam_rule["domain"]},
            "localhost",
        ],
        "queryStrategy": "UseIPv4",
    }
    assert config["fakedns"] == {
        "ipPool": "198.18.0.0/15",
        "poolSize": 65535,
    }
    assert {"protocol": "dns", "tag": "dns-out"} in config["outbounds"]

    rules = config["routing"]["rules"]
    dns_idx = next(i for i, rule in enumerate(rules) if rule.get("port") == 53)
    private_idx = next(
        i for i, rule in enumerate(rules) if rule.get("ip") == ["geoip:private"]
    )
    tun_idx = next(
        i
        for i, rule in enumerate(rules)
        if rule.get("inboundTag") == ["tun"] and rule.get("port") is None
    )
    assert rules[dns_idx] == {
        "type": "field",
        "inboundTag": ["tun"],
        "port": 53,
        "outboundTag": "dns-out",
    }
    assert dns_idx < private_idx < tun_idx

    for inbound in config["inbounds"]:
        if inbound["tag"] != "api":
            assert "fakedns" in inbound["sniffing"]["destOverride"]


def test_steam_download_cdn_fallback_does_not_direct_store_or_community():
    config = _build(
        {"protocol": "vless", "uuid": UUID, "address": "h.io", "port": 443},
        route_rules=[
            _rr(
                action="direct",
                match={"type": "geosite", "value": "geosite:steam@cn"},
            )
        ],
    )

    steam_rule = next(
        rule
        for rule in config["routing"]["rules"]
        if rule.get("domain") and "geosite:steam@cn" in rule["domain"]
    )
    assert steam_rule["outboundTag"] == "direct"
    assert "domain:steamcontent.com" in steam_rule["domain"]
    assert "domain:steampipe.akamaized.net" in steam_rule["domain"]
    assert "domain:steamcdn-a.akamaihd.net" in steam_rule["domain"]
    assert "store.steampowered.com" not in steam_rule["domain"]
    assert "steamcommunity.com" not in steam_rule["domain"]


def test_tun_mode_still_hijacks_dns_without_fake_dns_when_no_direct_domain_rule():
    config = _build(
        {"protocol": "vless", "uuid": UUID, "address": "h.io", "port": 443},
        tun_mode=True,
        outbound_interface="wlan0",
        route_rules=[
            _rr(
                action="proxy",
                match={"type": "geosite", "value": "geosite:google"},
            )
        ],
    )

    assert config["dns"] == {"servers": ["localhost"], "queryStrategy": "UseIPv4"}
    assert "fakedns" not in config
    for inbound in config["inbounds"]:
        if inbound["tag"] != "api":
            assert "fakedns" not in inbound["sniffing"]["destOverride"]


def test_no_tun_inbound_without_tun_mode():
    config = _build(
        {"protocol": "vless", "uuid": UUID, "address": "h.io", "port": 443}
    )
    assert all(i["protocol"] != "tun" for i in config["inbounds"])


# ----- Hysteria2 (xray-core, since v26.7.28) -----


def _hy2(**extra):
    profile = {
        "protocol": "hysteria2",
        "core": "xray-core",
        "password": "secret",
        "address": "h2.example.com",
        "port": 443,
        "tlsConfig": {"serverName": "h2.example.com"},
        "network": "udp",
        "security": "tls",
    }
    profile.update(extra)
    return profile


def test_hysteria2_basic_outbound():
    config = _build(_hy2())
    outbound = _proxy_outbound(config)
    # Xray v26.7.28 registers the native Hysteria v2 client as "hysteria".
    assert outbound["protocol"] == "hysteria"
    assert outbound["settings"] == {
        "version": 2,
        "address": "h2.example.com",
        "port": 443,
    }
    stream = outbound["streamSettings"]
    # "udp" is not a valid Xray stream transport. Hysteria has its own
    # transport name and must be explicit so the default does not become tcp.
    assert stream["network"] == "hysteria"
    assert stream["security"] == "tls"
    assert stream["tlsSettings"]["alpn"] == ["h3"]
    assert stream["hysteriaSettings"] == {"version": 2, "auth": "secret"}
    # No obfs requested — no finalmask emitted.
    assert "finalmask" not in stream


def test_hysteria2_tls_uses_pinning_without_removed_allow_insecure_or_utls():
    config = _build(
        _hy2(
            tlsConfig={
                "serverName": "h2.example.com",
                "alpn": ["h3"],
                "allowInsecure": True,
                "pinnedPeerCertSha256": "AA" * 32,
                "verifyPeerCertByName": "h2.example.com",
                "echConfigList": "ZWNoLWNvbmZpZw==",
                "fingerprint": "chrome",
            }
        )
    )
    tls = _proxy_outbound(config)["streamSettings"]["tlsSettings"]
    assert tls["alpn"] == ["h3"]
    assert tls["pinnedPeerCertSha256"] == "AA" * 32
    assert tls["verifyPeerCertByName"] == "h2.example.com"
    assert tls["echConfigList"] == "ZWNoLWNvbmZpZw=="
    assert "allowInsecure" not in tls
    assert "fingerprint" not in tls


def test_hysteria2_port_hopping_uses_finalmask_quic_params():
    config = _build(
        _hy2(portHopping={"ports": "21000-22000", "interval": "15"})
    )
    stream = _proxy_outbound(config)["streamSettings"]
    assert stream["finalmask"]["quicParams"]["udpHop"] == {
        "ports": "21000-22000",
        "interval": "15",
    }


def test_hysteria2_salamander_obfs_emits_finalmask_without_packetSize():
    config = _build(_hy2(obfs="salamander", obfsPassword="xyz"))
    stream = _proxy_outbound(config)["streamSettings"]
    assert "finalmask" in stream
    udp = stream["finalmask"]["udp"]
    assert len(udp) == 1
    entry = udp[0]
    assert entry["type"] == "salamander"
    # Standard salamander: packetSize MUST be absent (its presence triggers Gecko).
    assert "packetSize" not in entry["settings"]
    assert entry["settings"]["password"] == "xyz"


def test_hysteria2_gecko_emits_finalmask_with_packetSize():
    config = _build(
        _hy2(
            obfs="gecko",
            obfsPassword="gecko-pw",
            geckoEnabled=True,
        )
    )
    stream = _proxy_outbound(config)["streamSettings"]
    assert "finalmask" in stream
    entry = stream["finalmask"]["udp"][0]
    assert entry["type"] == "salamander"
    assert entry["settings"]["password"] == "gecko-pw"
    # Gecko is distinguished by packetSize (PR #6198); Xray's Int32Range
    # parser accepts the compact "from-to" form.
    assert entry["settings"]["packetSize"] == "1000-1500"


def test_hysteria2_does_not_emit_udp_transport_network():
    # Regression for "Config: unknown transport protocol: udp" — xray-core's
    # streamSettings.network is a transport-layer allow-list. Hysteria2 must
    # use Xray's "hysteria" transport name; the share-link's network="udp"
    # must never leak into the generated stream settings.
    config = _build(_hy2(network="tcp"))
    stream = _proxy_outbound(config)["streamSettings"]
    assert stream["network"] == "hysteria"
    # And the same holds when Gecko is enabled.
    config = _build(_hy2(network="tcp", obfs="gecko", obfsPassword="x", geckoEnabled=True))
    stream = _proxy_outbound(config)["streamSettings"]
    assert stream["network"] == "hysteria"
    assert "finalmask" in stream  # gecko finalmask must still be emitted


# ----- User-editable routing rules -----


def _rr(**overrides):
    rule = {
        "id": "r1",
        "enabled": True,
        "action": "proxy",
        "match": {"type": "domain", "value": "example.com"},
    }
    rule.update(overrides)
    return rule


def test_route_rules_empty_leaves_no_user_rules():
    config = _build(_hy2(), route_rules=[])
    rules = config["routing"]["rules"]
    # api -> api, geoip:private -> direct, then the built-in inbound rules.
    assert rules[0]["inboundTag"] == ["api"]
    assert rules[1]["ip"] == ["geoip:private"]
    assert not any(
        rule.get("outboundTag") == "block" for rule in rules
    ), "block tag should not appear without reject rule"
    assert "block" not in [o.get("tag") for o in config["outbounds"]]


def test_route_rules_domain_proxy_inserts_after_private_bypass():
    rules_in = [_rr()]
    config = _build(_hy2(), route_rules=rules_in)
    rules = config["routing"]["rules"]
    private_idx = next(
        i for i, r in enumerate(rules) if r.get("ip") == ["geoip:private"]
    )
    user_idx = next(
        i
        for i, r in enumerate(rules)
        if r.get("domain") == ["example.com"]
    )
    assert private_idx < user_idx, "LAN bypass must come before user rules"


def test_tun_catch_all_does_not_shadow_user_route_rules():
    config = _build(
        _hy2(),
        tun_mode=True,
        outbound_interface="wlan0",
        route_rules=[
            _rr(
                action="direct",
                match={"type": "geosite", "value": "geosite:steam@cn"},
            )
        ],
    )
    rules = config["routing"]["rules"]
    user_idx = next(
        i
        for i, rule in enumerate(rules)
        if rule.get("domain") and "geosite:steam@cn" in rule["domain"]
    )
    tun_idx = next(
        i
        for i, rule in enumerate(rules)
        if rule.get("inboundTag") == ["tun"] and rule.get("port") is None
    )
    assert user_idx < tun_idx, "TUN catch-all must come after user rules"


def test_route_rules_geoip_direct():
    config = _build(
        _hy2(),
        route_rules=[
            _rr(action="direct", match={"type": "geoip", "value": "geoip:cn"})
        ],
    )
    user = next(
        r
        for r in config["routing"]["rules"]
        if r.get("ip") == ["geoip:cn"]
    )
    assert user["outboundTag"] == "direct"


def test_route_rules_reject_emits_blackhole_outbound():
    config = _build(
        _hy2(),
        route_rules=[
            _rr(action="reject", match={"type": "ip", "value": "1.2.3.0/24"})
        ],
    )
    tags = [o.get("tag") for o in config["outbounds"]]
    assert "block" in tags
    block_outbound = next(o for o in config["outbounds"] if o.get("tag") == "block")
    assert block_outbound["protocol"] == "blackhole"
    user = next(
        r
        for r in config["routing"]["rules"]
        if r.get("ip") == ["1.2.3.0/24"]
    )
    assert user["outboundTag"] == "block"


def test_route_rules_disabled_rule_is_skipped():
    config = _build(
        _hy2(),
        route_rules=[_rr(enabled=False, match={"type": "domain", "value": "x.com"})],
    )
    assert not any(
        r.get("domain") == ["x.com"] for r in config["routing"]["rules"]
    )
    # Disabled rule means no reject -> no blackhole outbound either.
    assert "block" not in [o.get("tag") for o in config["outbounds"]]


def test_route_rules_unknown_action_skipped_silently():
    config = _build(
        _hy2(),
        route_rules=[_rr(action="redirect", match={"type": "ip", "value": "1.1.1.1"})],
    )
    assert not any(
        r.get("ip") == ["1.1.1.1"] for r in config["routing"]["rules"]
    )


# ----- route_rules through the public generate_config wrapper -----


def test_generate_config_accepts_route_rules_kwarg(tmp_path):
    """The public wrapper must thread route_rules through to the builder.

    Regression test for the wired-up-but-not-passed-through bug: the
    internal _build_xray_config takes the kwarg, but main.py calls the
    public generate_config — if the wrapper drops it, the running core
    silently ships without user rules.
    """
    mgr = XrayManager()
    config_file = mgr.generate_config(
        {
            "protocol": "vless",
            "uuid": UUID,
            "address": "h.io",
            "port": 443,
        },
        route_rules=[
            {
                "id": "r1",
                "enabled": True,
                "action": "direct",
                "match": {"type": "geosite", "value": "geosite:cn"},
            }
        ],
    )
    try:
        assert config_file.endswith(".json")
        with open(config_file) as f:
            rendered = json.load(f)
        rules = rendered["routing"]["rules"]
        # User rule must land in the right slot (after the LAN bypass).
        user = next(r for r in rules if r.get("domain") == ["geosite:cn"])
        assert user["outboundTag"] == "direct"
    finally:
        os.unlink(config_file)
