"""Tests for backend.src.singbox_manager (config generation + lifecycle)."""

import asyncio
import json
import os

import pytest

from backend.src.singbox_manager import (
    HTTP_PORT,
    SOCKS_PORT,
    SingBoxManager,
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
    # An explicit address is required for the interface to come up so the
    # external default-route setup can succeed.
    assert tun["address"] == ["172.19.0.1/30"]
    assert _proxy(config)["bind_interface"] == "wlan0"


def test_tun_mode_binds_direct_outbound_to_physical_interface():
    config = build_singbox_config(
        _hysteria2(), tun_mode=True, outbound_interface="wlan0"
    )
    direct = next(outbound for outbound in config["outbounds"] if outbound["tag"] == "direct")
    assert direct["bind_interface"] == "wlan0"


def test_unsupported_protocol_raises():
    with pytest.raises(ValueError):
        build_singbox_config({"protocol": "vless", "address": "h.io", "port": 443})


# --- process lifecycle ---


def _fake_binary(tmp_path, script: str) -> str:
    path = tmp_path / "sing-box"
    path.write_text(f"#!/bin/sh\n{script}\n")
    os.chmod(path, 0o755)
    return str(path)


def test_start_missing_binary(tmp_path):
    manager = SingBoxManager(binary_path=str(tmp_path / "absent"))
    result = asyncio.run(manager.start("/tmp/whatever.json"))
    assert result["success"] is False
    assert result["errorCode"] == "BINARY_NOT_FOUND"


def test_start_stop_roundtrip(tmp_path):
    manager = SingBoxManager(binary_path=_fake_binary(tmp_path, "sleep 30"))
    config_file = tmp_path / "config.json"
    config_file.write_text("{}")

    async def run():
        result = await manager.start(str(config_file))
        assert result["success"] is True
        assert result["processId"] == manager.get_process_id()
        assert manager.is_running() is True

        stop = await manager.stop()
        assert stop["success"] is True
        assert manager.is_running() is False
        assert manager.get_process_id() is None

    asyncio.run(run())
    # stop() removes the temp config file it was started with.
    assert not config_file.exists()


def test_start_captures_immediate_failure(tmp_path):
    manager = SingBoxManager(
        binary_path=_fake_binary(tmp_path, 'echo "bad config" >&2; exit 1')
    )
    result = asyncio.run(manager.start("/tmp/whatever.json"))
    assert result["success"] is False
    assert result["errorCode"] == "PROCESS_START_FAILED"
    assert "bad config" in result["error"]


def test_stop_without_process():
    manager = SingBoxManager(binary_path="/nonexistent/sing-box")
    result = asyncio.run(manager.stop())
    assert result["success"] is True


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


def test_route_rules_default_empty_leaves_only_lan_bypass():
    config = build_singbox_config(_hysteria2())
    rules = config["route"]["rules"]
    assert len(rules) == 1
    assert rules[0]["ip_is_private"] is True


def test_route_rules_domain_inserts_after_lan_bypass():
    config = build_singbox_config(_hysteria2(), route_rules=[_rr()])
    rules = config["route"]["rules"]
    assert rules[0]["ip_is_private"] is True
    assert rules[1]["domain"] == ["example.com"]
    assert rules[1]["outbound"] == "proxy"
    assert config["route"]["final"] == "proxy"


def test_route_rules_geoip_strips_prefix():
    config = build_singbox_config(
        _hysteria2(),
        route_rules=[_rr(action="direct", match={"type": "geoip", "value": "geoip:cn"})],
    )
    rules = config["route"]["rules"]
    user = next(r for r in rules if r.get("rule_set") == ["geoip-cn"])
    assert user["outbound"] == "direct"


def test_route_rules_use_local_rule_set_tags(tmp_path):
    config = build_singbox_config(
        _hysteria2(),
        rule_set_dir=str(tmp_path),
        route_rules=[
            _rr(
                action="direct",
                match={"type": "geosite", "value": "geosite:category-games@cn"},
            ),
            _rr(
                action="proxy",
                match={"type": "geoip", "value": "geoip:private"},
            ),
        ],
    )
    definitions = config["route"]["rule_set"]
    assert len(definitions) == 19
    assert all(item["type"] == "local" for item in definitions)
    assert all(item["format"] == "binary" for item in definitions)
    assert all(item["path"].startswith(str(tmp_path)) for item in definitions)

    game_rule = next(
        r
        for r in config["route"]["rules"]
        if r.get("rule_set") == ["geosite-category-games@cn"]
    )
    assert game_rule["outbound"] == "direct"
    private_rule = next(
        r
        for r in config["route"]["rules"]
        if r.get("rule_set") == ["geoip-private"]
    )
    assert private_rule["outbound"] == "proxy"
    assert not any("geosite" in r or "geoip" in r for r in config["route"]["rules"])


def test_route_rules_reject_uses_builtin_block():
    config = build_singbox_config(
        _hysteria2(),
        route_rules=[_rr(action="reject", match={"type": "ip", "value": "1.2.3.0/24"})],
    )
    user = next(r for r in config["route"]["rules"] if r.get("ip_cidr"))
    assert user["outbound"] == "block"


def test_route_rules_disabled_skipped():
    config = build_singbox_config(
        _hysteria2(),
        route_rules=[_rr(enabled=False, match={"type": "domain", "value": "x.com"})],
    )
    assert not any("domain" in r for r in config["route"]["rules"])


def test_manager_generate_config_persists_rule_set_directory(tmp_path):
    manager = SingBoxManager(binary_path=str(tmp_path / "sing-box"))
    config_path = manager.generate_config(
        _hysteria2(),
        rule_set_dir=tmp_path,
        route_rules=[
            _rr(
                match={"type": "geosite", "value": "geosite:cn"},
            )
        ],
    )
    with open(config_path, encoding="utf-8") as stream:
        config = json.load(stream)
    assert manager.rule_set_dir == str(tmp_path.resolve())
    assert all(
        item["path"].startswith(str(tmp_path.resolve()))
        for item in config["route"]["rule_set"]
    )
    os.remove(config_path)
