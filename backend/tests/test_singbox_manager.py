"""Tests for backend.src.singbox_manager (sing-box config generation)."""

import pytest

from backend.src.singbox_manager import (
    HTTP_PORT,
    SOCKS_PORT,
    build_singbox_config,
)


UUID = "a5a075d3-b3d5-4a03-b2e0-8a1f04b1cf75"


def _hysteria2(**extra):
    profile = {
        "protocol": "hysteria2",
        "core": "sing-box",
        "password": "pw",
        "address": "h2.example.com",
        "port": 443,
        "tlsConfig": {"serverName": "h2.example.com"},
    }
    profile.update(extra)
    return profile


def _tuic(**extra):
    profile = {
        "protocol": "tuic",
        "core": "sing-box",
        "uuid": UUID,
        "password": "pw",
        "address": "t.example.com",
        "port": 443,
        "tlsConfig": {"serverName": "t.example.com", "alpn": ["h3"]},
    }
    profile.update(extra)
    return profile


def _proxy(config):
    return next(o for o in config["outbounds"] if o.get("tag") == "proxy")


def test_hysteria2_outbound():
    config = build_singbox_config(_hysteria2(obfs="salamander", obfsPassword="xyz"))
    proxy = _proxy(config)
    assert proxy["type"] == "hysteria2"
    assert proxy["server"] == "h2.example.com"
    assert proxy["server_port"] == 443
    assert proxy["password"] == "pw"
    assert proxy["tls"] == {"enabled": True, "server_name": "h2.example.com"}
    assert proxy["obfs"] == {"type": "salamander", "password": "xyz"}


def test_hysteria2_insecure_tls():
    profile = _hysteria2(tlsConfig={"serverName": "h2.example.com", "allowInsecure": True})
    proxy = _proxy(build_singbox_config(profile))
    assert proxy["tls"]["insecure"] is True


def test_tuic_outbound():
    config = build_singbox_config(
        _tuic(congestionControl="bbr", udpRelayMode="native")
    )
    proxy = _proxy(config)
    assert proxy["type"] == "tuic"
    assert proxy["uuid"] == UUID
    assert proxy["password"] == "pw"
    assert proxy["congestion_control"] == "bbr"
    assert proxy["udp_relay_mode"] == "native"
    assert proxy["tls"]["alpn"] == ["h3"]


def test_default_inbounds_and_route():
    config = build_singbox_config(_hysteria2())
    inbound_ports = {
        i["type"]: i.get("listen_port") for i in config["inbounds"]
    }
    assert inbound_ports["socks"] == SOCKS_PORT
    assert inbound_ports["http"] == HTTP_PORT
    assert all(i["type"] != "tun" for i in config["inbounds"])
    tags = [o["tag"] for o in config["outbounds"]]
    assert tags == ["proxy", "direct"]
    assert config["route"]["final"] == "proxy"
    assert config["route"]["rules"][0] == {
        "ip_is_private": True,
        "outbound": "direct",
    }


def test_tun_mode_adds_inbound_and_binds_interface():
    config = build_singbox_config(
        _hysteria2(), tun_mode=True, outbound_interface="wlan0"
    )
    tun = next(i for i in config["inbounds"] if i["type"] == "tun")
    assert tun["interface_name"] == "xray0"
    assert tun["auto_route"] is False
    assert _proxy(config)["bind_interface"] == "wlan0"


def test_unsupported_protocol_raises():
    with pytest.raises(ValueError):
        build_singbox_config({"protocol": "vless", "address": "h.io", "port": 443})
