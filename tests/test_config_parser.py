"""Tests for backend.src.config_parser (share-link parsing)."""

import base64
import json

from backend.src.config_parser import (
    build_profile_config,
    core_for_protocol,
    core_rejection_reason,
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


# --- SOCKS ---


def test_socks_with_credentials():
    profile = parse_share_link("socks://user:p%40ss@192.168.1.5:1080#Phone")
    assert profile is not None
    assert profile["protocol"] == "socks"
    assert profile["username"] == "user"
    assert profile["password"] == "p@ss"
    assert profile["address"] == "192.168.1.5"
    assert profile["port"] == 1080
    assert profile["network"] == "tcp"
    assert profile["security"] == "none"
    assert profile["core"] == "xray"
    assert profile["name"] == "Phone"


def test_socks5_alias_without_credentials():
    profile = parse_share_link("socks5://192.168.1.5:1080#LAN")
    assert profile is not None
    assert profile["protocol"] == "socks"
    assert "username" not in profile
    assert "password" not in profile
    assert profile["name"] == "LAN"


def test_socks_base64_userinfo():
    userinfo = base64.urlsafe_b64encode(b"alice:s3cret").decode().rstrip("=")
    profile = parse_share_link(f"socks://{userinfo}@10.0.0.2:1080")
    assert profile["username"] == "alice"
    assert profile["password"] == "s3cret"


def test_socks_username_only():
    profile = parse_share_link("socks://alice@10.0.0.2:1080")
    assert profile["username"] == "alice"
    assert "password" not in profile


def test_socks_rejects_bad_endpoint():
    assert parse_share_link("socks://10.0.0.2:99999") is None
    assert parse_share_link("socks://10.0.0.2") is None


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
        # VLESS/Trojan carry security=tls: xray-core refuses either protocol
        # without transport security when the server is on a public address.
        f"vless://{UUID_V4}@example.com:443?security=tls&sni=example.com",
        "trojan://pw@example.com:443?security=tls&sni=example.com",
        f"ss://{userinfo}@example.com:8388",
        f"vmess://{_b64(json.dumps({'add': 'h.io', 'port': 443, 'id': UUID_V4}))}",
    ):
        is_valid, error = validate_share_link(url)
        assert is_valid, f"{url}: {error}"


def test_validate_accepts_socks():
    assert validate_share_link("socks://192.168.1.5:1080")[0]
    assert validate_share_link("socks5://user:pw@192.168.1.5:1080")[0]


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


def test_vless_tls_parses_cert_pinning_params():
    pin = "b" * 64
    url = (
        f"vless://{UUID_V4}@example.com:443"
        f"?type=tcp&security=tls&sni=example.com&pcs={pin}"
        "&vcn=a.example.com%2Cb.example.com#PIN"
    )
    profile = parse_share_link(url)
    assert profile["tlsConfig"] == {
        "serverName": "example.com",
        "pinnedPeerCertSha256": pin,
        "verifyPeerCertByName": "a.example.com,b.example.com",
    }


def test_vless_tls_accepts_long_form_cert_pinning_params():
    pin = "C" * 64
    url = (
        f"vless://{UUID_V4}@example.com:443"
        f"?type=tcp&security=tls&pinnedPeerCertSha256={pin}"
        "&verifyPeerCertByName=a.example.com#PIN"
    )
    profile = parse_share_link(url)
    assert profile["tlsConfig"]["pinnedPeerCertSha256"] == "c" * 64
    assert profile["tlsConfig"]["verifyPeerCertByName"] == "a.example.com"


def test_vless_tls_drops_malformed_cert_pins():
    # xray-core refuses to start on a bad pin, so a malformed one must never
    # reach the generated config.
    good = "d" * 64
    url = (
        f"vless://{UUID_V4}@example.com:443"
        f"?type=tcp&security=tls&pcs=nothex%2C{good}%2Cabc#PIN"
    )
    profile = parse_share_link(url)
    assert profile["tlsConfig"]["pinnedPeerCertSha256"] == good


def test_vless_tls_omits_cert_pinning_when_all_pins_are_malformed():
    url = (
        f"vless://{UUID_V4}@example.com:443"
        "?type=tcp&security=tls&pcs=abc&vcn=%20#PIN"
    )
    profile = parse_share_link(url)
    tls = profile.get("tlsConfig") or {}
    assert "pinnedPeerCertSha256" not in tls
    assert "verifyPeerCertByName" not in tls


def _ss_link(method: str, host: str = "example.com") -> str:
    userinfo = base64.urlsafe_b64encode(f"{method}:pw".encode()).decode().rstrip("=")
    return f"ss://{userinfo}@{host}:8388#S"


def test_removed_shadowsocks_ciphers_are_rejected_at_import():
    for method in ("none", "plain"):
        ok, error = validate_share_link(_ss_link(method))
        assert ok is False
        assert method in error
        assert "aes-256-gcm" in error


def test_supported_shadowsocks_ciphers_still_import():
    for method in ("aes-256-gcm", "chacha20-ietf-poly1305"):
        assert validate_share_link(_ss_link(method)) == (True, None)


def test_vless_without_transport_security_to_public_address_is_rejected():
    for host in ("example.com", "1.2.3.4", "8.8.8.8"):
        ok, error = validate_share_link(
            f"vless://{UUID_V4}@{host}:443?type=tcp&security=none#A"
        )
        assert ok is False, host
        assert "VLESS" in error and "TLS" in error


def test_trojan_without_tls_to_public_address_is_rejected():
    ok, error = validate_share_link(
        "trojan://pw@example.com:443?type=tcp&security=none#A"
    )
    assert ok is False
    assert "TROJAN" in error


def test_no_transport_security_is_allowed_on_private_addresses():
    # Matches what xray-core counts as private (geoip/geosite private).
    for host in ("192.168.1.5", "10.0.0.5", "127.0.0.1", "nas.local", "box.lan",
                 "srv.internal", "myserver", "x.y.local"):
        assert validate_share_link(
            f"vless://{UUID_V4}@{host}:443?type=tcp&security=none#A"
        ) == (True, None), host


def test_transport_security_keeps_public_addresses_importable():
    assert validate_share_link(
        f"vless://{UUID_V4}@example.com:443?type=tcp&security=tls&sni=example.com#A"
    ) == (True, None)
    assert validate_share_link(
        f"vless://{UUID_V4}@1.2.3.4:443?type=tcp&security=reality"
        "&pbk=PUB&sid=ab&sni=example.com&fp=chrome#A"
    ) == (True, None)


def test_singbox_protocols_are_not_judged_by_xray_rules():
    # hysteria2/tuic run on sing-box, which has none of these restrictions.
    assert core_rejection_reason(
        {"core": "sing-box", "protocol": "hysteria2", "address": "example.com"}
    ) is None


def test_vmess_and_socks_without_tls_are_unaffected():
    for profile in (
        {"protocol": "vmess", "address": "example.com", "security": "none"},
        {"protocol": "socks", "address": "example.com", "security": "none"},
    ):
        assert core_rejection_reason(profile) is None
