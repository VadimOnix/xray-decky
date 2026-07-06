"""Tests for backend.src.config_parser (share-link parsing)."""

import base64
import json

from backend.src.config_parser import (
    build_profile_config,
    core_for_protocol,
    parse_share_link,
    parse_subscription,
    validate_share_link,
)


UUID_V4 = "a5a075d3-b3d5-4a03-b2e0-8a1f04b1cf75"
UUID_V1 = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"


def _b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


# --- VLESS ---


def test_vless_reality_tcp():
    url = (
        f"vless://{UUID_V4}@1.2.3.4:443"
        "?type=tcp&security=reality&pbk=PUBKEY&sid=ab12&sni=example.com"
        "&fp=chrome&flow=xtls-rprx-vision&spx=%2F#My%20Server"
    )
    profile = parse_share_link(url)
    assert profile is not None
    assert profile["protocol"] == "vless"
    assert profile["uuid"] == UUID_V4
    assert profile["address"] == "1.2.3.4"
    assert profile["port"] == 443
    assert profile["network"] == "tcp"
    assert profile["security"] == "reality"
    assert profile["flow"] == "xtls-rprx-vision"
    assert profile["realityConfig"] == {
        "publicKey": "PUBKEY",
        "shortId": "ab12",
        "serverName": "example.com",
        "fingerprint": "chrome",
        "spiderX": "/",
    }
    assert profile["name"] == "My Server"


def test_vless_ws_tls_honors_path_host_sni_alpn():
    url = (
        f"vless://{UUID_V4}@example.com:443"
        "?type=ws&security=tls&path=%2Fws%3Fx%3D1&host=cdn.example.com"
        "&sni=cdn.example.com&alpn=h2%2Chttp%2F1.1&fp=firefox&allowInsecure=1#WS"
    )
    profile = parse_share_link(url)
    assert profile["network"] == "ws"
    assert profile["transport"] == {"path": "/ws?x=1", "host": "cdn.example.com"}
    assert profile["tlsConfig"] == {
        "serverName": "cdn.example.com",
        "alpn": ["h2", "http/1.1"],
        "fingerprint": "firefox",
        "allowInsecure": True,
    }


def test_vless_grpc():
    url = (
        f"vless://{UUID_V4}@h.example.com:443"
        "?type=grpc&security=tls&serviceName=svc&mode=multi&authority=a.example.com"
    )
    profile = parse_share_link(url)
    assert profile["network"] == "grpc"
    assert profile["transport"] == {
        "serviceName": "svc",
        "authority": "a.example.com",
        "multiMode": True,
    }


def test_vless_httpupgrade_and_xhttp():
    hu = parse_share_link(
        f"vless://{UUID_V4}@example.com:80?type=httpupgrade&path=%2Fup&host=h.io"
    )
    assert hu["network"] == "httpupgrade"
    assert hu["transport"] == {"path": "/up", "host": "h.io"}

    xh = parse_share_link(
        f"vless://{UUID_V4}@example.com:443"
        "?type=xhttp&security=tls&path=%2Fxh&mode=packet-up"
    )
    assert xh["network"] == "xhttp"
    assert xh["transport"] == {"path": "/xh", "mode": "packet-up"}


def test_vless_splithttp_normalized_to_xhttp():
    profile = parse_share_link(
        f"vless://{UUID_V4}@example.com:443?type=splithttp&path=%2Fs"
    )
    assert profile["network"] == "xhttp"


def test_vless_kcp_with_seed():
    profile = parse_share_link(
        f"vless://{UUID_V4}@1.2.3.4:8388?type=mkcp&headerType=dtls&seed=s3cret"
    )
    assert profile["network"] == "kcp"
    assert profile["transport"] == {"headerType": "dtls", "seed": "s3cret"}


def test_vless_accepts_non_v4_uuid():
    profile = parse_share_link(f"vless://{UUID_V1}@example.com:443?security=tls")
    assert profile is not None
    assert profile["uuid"] == UUID_V1


def test_vless_ipv6_host():
    profile = parse_share_link(f"vless://{UUID_V4}@[2001:db8::1]:443?type=tcp")
    assert profile is not None
    assert profile["address"] == "2001:db8::1"


def test_vless_encryption_passthrough():
    profile = parse_share_link(
        f"vless://{UUID_V4}@example.com:443?encryption=mlkem768x25519plus.native.0rtt.KEY"
    )
    assert profile["encryption"] == "mlkem768x25519plus.native.0rtt.KEY"


def test_vless_rejects_bad_uuid_and_port():
    assert parse_share_link("vless://not-a-uuid@example.com:443") is None
    assert parse_share_link(f"vless://{UUID_V4}@example.com:99999") is None
    assert parse_share_link(f"vless://{UUID_V4}@:443") is None


# --- Trojan ---


def test_trojan_defaults_to_tls():
    profile = parse_share_link(
        "trojan://p%40ssword@example.com:443?sni=example.com#Troj"
    )
    assert profile["protocol"] == "trojan"
    assert profile["password"] == "p@ssword"
    assert profile["security"] == "tls"
    assert profile["tlsConfig"] == {"serverName": "example.com"}
    assert profile["name"] == "Troj"


def test_trojan_ws_transport():
    profile = parse_share_link(
        "trojan://pw@example.com:443?type=ws&path=%2Ft&host=cdn.io"
    )
    assert profile["network"] == "ws"
    assert profile["transport"] == {"path": "/t", "host": "cdn.io"}


def test_trojan_requires_password():
    assert parse_share_link("trojan://@example.com:443") is None


# --- Shadowsocks ---


def test_ss_sip002_base64_userinfo():
    userinfo = base64.urlsafe_b64encode(b"aes-256-gcm:secret-pass").decode().rstrip("=")
    profile = parse_share_link(f"ss://{userinfo}@1.2.3.4:8388#SS%20Node")
    assert profile["protocol"] == "shadowsocks"
    assert profile["method"] == "aes-256-gcm"
    assert profile["password"] == "secret-pass"
    assert profile["address"] == "1.2.3.4"
    assert profile["port"] == 8388
    assert profile["name"] == "SS Node"


def test_ss_2022_plain_userinfo():
    profile = parse_share_link(
        "ss://2022-blake3-aes-256-gcm:cGFzc3dvcmQ%3D@example.com:8388#2022"
    )
    assert profile["method"] == "2022-blake3-aes-256-gcm"
    assert profile["password"] == "cGFzc3dvcmQ="


def test_ss_legacy_full_base64():
    encoded = _b64("chacha20-ietf-poly1305:pass:with:colons@example.com:8388")
    profile = parse_share_link(f"ss://{encoded}#Legacy")
    assert profile["method"] == "chacha20-ietf-poly1305"
    assert profile["password"] == "pass:with:colons"
    assert profile["address"] == "example.com"
    assert profile["port"] == 8388


def test_ss_rejects_sip003_plugin():
    userinfo = base64.urlsafe_b64encode(b"aes-256-gcm:pw").decode().rstrip("=")
    url = f"ss://{userinfo}@1.2.3.4:8388/?plugin=obfs-local%3Bobfs%3Dhttp"
    assert parse_share_link(url) is None


# --- VMess ---


def test_vmess_ws_tls():
    payload = {
        "v": "2",
        "ps": "VMess WS",
        "add": "example.com",
        "port": "443",
        "id": UUID_V4,
        "aid": "0",
        "scy": "auto",
        "net": "ws",
        "type": "none",
        "host": "cdn.example.com",
        "path": "/vm",
        "tls": "tls",
        "sni": "cdn.example.com",
        "alpn": "http/1.1",
        "fp": "chrome",
    }
    profile = parse_share_link(f"vmess://{_b64(json.dumps(payload))}")
    assert profile["protocol"] == "vmess"
    assert profile["uuid"] == UUID_V4
    assert profile["port"] == 443
    assert profile["network"] == "ws"
    assert profile["security"] == "tls"
    assert profile["alterId"] == 0
    assert profile["vmessSecurity"] == "auto"
    assert profile["transport"] == {"path": "/vm", "host": "cdn.example.com"}
    assert profile["tlsConfig"] == {
        "serverName": "cdn.example.com",
        "alpn": ["http/1.1"],
        "fingerprint": "chrome",
    }
    assert profile["name"] == "VMess WS"


def test_vmess_grpc_maps_path_to_service_name():
    payload = {"add": "h.io", "port": 443, "id": UUID_V4, "net": "grpc", "path": "svc"}
    profile = parse_share_link(f"vmess://{_b64(json.dumps(payload))}")
    assert profile["network"] == "grpc"
    assert profile["transport"]["serviceName"] == "svc"


def test_vmess_rejects_garbage():
    assert parse_share_link("vmess://%%%") is None
    assert parse_share_link(f"vmess://{_b64('not json')}") is None
    assert parse_share_link(f"vmess://{_b64('[1,2]')}") is None


# --- Hysteria2 / TUIC (sing-box core) ---


def test_hysteria2_link():
    profile = parse_share_link(
        "hysteria2://p%40ss@h2.example.com:443"
        "?sni=h2.example.com&insecure=1&obfs=salamander&obfs-password=xyz#HY2"
    )
    assert profile is not None
    assert profile["protocol"] == "hysteria2"
    assert profile["core"] == "sing-box"
    assert profile["password"] == "p@ss"
    assert profile["address"] == "h2.example.com"
    assert profile["port"] == 443
    assert profile["tlsConfig"] == {
        "serverName": "h2.example.com",
        "allowInsecure": True,
    }
    assert profile["obfs"] == "salamander"
    assert profile["obfsPassword"] == "xyz"
    assert profile["name"] == "HY2"


def test_hy2_alias():
    profile = parse_share_link("hy2://pw@h2.example.com:8443?sni=a.example.com")
    assert profile["protocol"] == "hysteria2"
    assert profile["core"] == "sing-box"


def test_tuic_link():
    profile = parse_share_link(
        f"tuic://{UUID_V4}:secret@t.example.com:443"
        "?congestion_control=bbr&alpn=h3&sni=t.example.com&udp_relay_mode=native#TUIC"
    )
    assert profile["protocol"] == "tuic"
    assert profile["core"] == "sing-box"
    assert profile["uuid"] == UUID_V4
    assert profile["password"] == "secret"
    assert profile["congestionControl"] == "bbr"
    assert profile["udpRelayMode"] == "native"
    assert profile["tlsConfig"]["alpn"] == ["h3"]


def test_tuic_requires_valid_uuid():
    assert parse_share_link("tuic://not-a-uuid:pw@t.example.com:443") is None


def test_xray_protocols_tagged_with_core():
    profile = parse_share_link(f"vless://{UUID_V4}@example.com:443?security=tls")
    assert profile["core"] == "xray"


def test_core_for_protocol():
    assert core_for_protocol("vless") == "xray"
    assert core_for_protocol("shadowsocks") == "xray"
    assert core_for_protocol("hysteria2") == "sing-box"
    assert core_for_protocol("tuic") == "sing-box"


def test_subscription_keeps_mixed_cores():
    links = "\n".join(
        [
            f"vless://{UUID_V4}@a.example.com:443?security=tls",
            "hysteria2://pw@h2.example.com:443",
            f"tuic://{UUID_V4}:pw@t.example.com:443",
        ]
    )
    profiles = parse_subscription(_b64(links))
    assert [p["core"] for p in profiles] == ["xray", "sing-box", "sing-box"]


# --- Subscriptions ---


def test_subscription_newline_delimited():
    links = "\n".join(
        [
            f"vless://{UUID_V4}@a.example.com:443?security=tls",
            "trojan://pw@b.example.com:443",
            "garbage-line",
        ]
    )
    profiles = parse_subscription(_b64(links))
    assert [p["protocol"] for p in profiles] == ["vless", "trojan"]


def test_subscription_legacy_json_array():
    links = json.dumps([f"vless://{UUID_V4}@a.example.com:443"])
    profiles = parse_subscription(_b64(links))
    assert len(profiles) == 1
    assert profiles[0]["address"] == "a.example.com"


def test_subscription_invalid_payloads():
    assert parse_subscription("!!!not-base64!!!") == []
    assert parse_subscription(_b64("just some text")) == []


# --- validate_share_link ---


def test_validate_accepts_all_supported_schemes():
    userinfo = base64.urlsafe_b64encode(b"aes-256-gcm:pw").decode().rstrip("=")
    for url in (
        f"vless://{UUID_V4}@example.com:443",
        "trojan://pw@example.com:443",
        f"ss://{userinfo}@example.com:8388",
        f"vmess://{_b64(json.dumps({'add': 'h.io', 'port': 443, 'id': UUID_V4}))}",
    ):
        is_valid, error = validate_share_link(url)
        assert is_valid, f"{url}: {error}"


def test_validate_accepts_hysteria2_and_tuic():
    assert validate_share_link("hysteria2://pw@h2.example.com:443")[0]
    assert validate_share_link(f"tuic://{UUID_V4}:pw@t.example.com:443")[0]


def test_validate_rejects_unsupported_scheme_with_hint():
    is_valid, error = validate_share_link("naive+https://x@example.com:443")
    assert not is_valid
    assert error


def test_validate_rejects_garbage():
    is_valid, error = validate_share_link("hello world")
    assert not is_valid
    assert error


# --- build_profile_config ---


def test_build_profile_config_adds_metadata():
    parsed = parse_share_link(f"vless://{UUID_V4}@example.com:443?security=tls")
    config = build_profile_config(parsed, "vless://source", "single")
    assert config["sourceUrl"] == "vless://source"
    assert config["configType"] == "single"
    assert config["isValid"] is True
    assert isinstance(config["importedAt"], int)
    # The parsed dict is not mutated.
    assert "sourceUrl" not in parsed
