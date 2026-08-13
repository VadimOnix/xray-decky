"""
Share-link parser for xray-supported protocols.

Parses and validates share links (VLESS, VMess, Trojan, Shadowsocks) and
base64 subscriptions into a protocol-agnostic profile dictionary consumed
by xray_manager to generate the xray-core config.
"""

import base64
import binascii
import json
import re
import urllib.parse
from ipaddress import ip_address
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID


SUPPORTED_SCHEMES = (
    "vless",
    "vmess",
    "trojan",
    "ss",
    "socks",
    "socks5",
    "hysteria2",
    "hy2",
    "tuic",
)

# Which core each protocol runs on. xray-core handles the classic protocols;
# hysteria2/tuic need the sing-box second core.
_XRAY_PROTOCOLS = ("vless", "vmess", "trojan", "shadowsocks", "socks")
_SINGBOX_PROTOCOLS = ("hysteria2", "tuic")


def core_for_protocol(protocol: str) -> str:
    """Return the core ('xray' or 'sing-box') that runs a given protocol."""
    return "sing-box" if protocol in _SINGBOX_PROTOCOLS else "xray"

# Legacy transport names normalized to what current xray-core expects.
_NETWORK_ALIASES = {"raw": "tcp", "mkcp": "kcp", "splithttp": "xhttp"}

_HOSTNAME_PATTERN = re.compile(
    r"^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?)*$",
    re.IGNORECASE,
)
_IPV4_SHAPE = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
_BASE64_CHARS = re.compile(r"^[A-Za-z0-9+/_=\-\s]+$")


def validate_uuid(uuid_string: str) -> bool:
    """Accept any RFC-4122 UUID (panels emit non-v4 UUIDs) in canonical form."""
    try:
        parsed = UUID(uuid_string)
    except (ValueError, AttributeError, TypeError):
        return False
    # Require the canonical dashed form: xray treats non-canonical strings
    # as custom IDs (mapped to UUIDv5), which would silently mismatch.
    return str(parsed) == uuid_string.lower()


def validate_port(port: int) -> bool:
    """Port must be an integer in 1-65535."""
    try:
        return 1 <= int(port) <= 65535
    except (ValueError, TypeError):
        return False


def validate_hostname(hostname: str) -> bool:
    """Accept hostnames, IPv4 and IPv6 addresses."""
    if not hostname or len(hostname) > 253:
        return False

    try:
        ip_address(hostname)
        return True
    except ValueError:
        pass

    # Looks like an IPv4 address but failed to parse (e.g. 1.2.3.999):
    # reject instead of falling through to the hostname check.
    if _IPV4_SHAPE.match(hostname):
        return False

    return bool(_HOSTNAME_PATTERN.match(hostname))


def _decode_base64(text: str) -> Optional[str]:
    """Tolerant base64 decode (standard + URL-safe, missing padding OK)."""
    if not text or not isinstance(text, str):
        return None
    text = text.strip()
    if not text or not _BASE64_CHARS.match(text):
        return None
    compact = re.sub(r"\s+", "", text)
    padded = compact + "=" * (-len(compact) % 4)
    for altchars in (None, b"-_"):
        try:
            # validate=True so URL-safe input never mis-decodes with the
            # standard alphabet (invalid characters raise instead of being
            # silently discarded).
            return base64.b64decode(padded, altchars=altchars, validate=True).decode(
                "utf-8"
            )
        except (binascii.Error, ValueError, UnicodeDecodeError):
            continue
    return None


def _parse_query(query: str) -> Dict[str, str]:
    """Parse a query string into a flat dict (last value wins)."""
    params: Dict[str, str] = {}
    for key, value in urllib.parse.parse_qsl(query, keep_blank_values=True):
        params[key] = value
    return params


def _normalize_network(network: str) -> str:
    network = (network or "tcp").lower()
    return _NETWORK_ALIASES.get(network, network)


def _is_truthy(value: Optional[str]) -> bool:
    return (value or "").lower() in ("1", "true", "yes")


def _transport_from_params(network: str, params: Dict[str, str]) -> Dict[str, Any]:
    """Extract transport-specific settings from share-link query params."""
    transport: Dict[str, Any] = {}

    if network in ("ws", "httpupgrade", "xhttp"):
        if params.get("path"):
            transport["path"] = params["path"]
        if params.get("host"):
            transport["host"] = params["host"]
        if network == "xhttp" and params.get("mode"):
            transport["mode"] = params["mode"]
    elif network == "grpc":
        service_name = params.get("serviceName") or params.get("path")
        if service_name:
            transport["serviceName"] = service_name
        if params.get("authority"):
            transport["authority"] = params["authority"]
        if params.get("mode") == "multi":
            transport["multiMode"] = True
    elif network == "kcp":
        if params.get("headerType"):
            transport["headerType"] = params["headerType"]
        if params.get("seed"):
            transport["seed"] = params["seed"]
    elif network == "tcp":
        if params.get("headerType") and params["headerType"] != "none":
            transport["headerType"] = params["headerType"]
            if params.get("host"):
                transport["host"] = params["host"]
            if params.get("path"):
                transport["path"] = params["path"]

    return transport


def _tls_from_params(params: Dict[str, str]) -> Dict[str, Any]:
    """Extract tlsSettings fields from share-link query params."""
    tls: Dict[str, Any] = {}
    if params.get("sni"):
        tls["serverName"] = params["sni"]
    if params.get("alpn"):
        alpn = [a.strip() for a in params["alpn"].split(",") if a.strip()]
        if alpn:
            tls["alpn"] = alpn
    if params.get("fp"):
        tls["fingerprint"] = params["fp"]
    if _is_truthy(params.get("allowInsecure")) or _is_truthy(params.get("insecure")):
        tls["allowInsecure"] = True
    return tls


def _reality_from_params(params: Dict[str, str]) -> Dict[str, Any]:
    """Extract client-side realitySettings fields (never server-side keys)."""
    reality: Dict[str, Any] = {}
    public_key = params.get("pbk") or params.get("publicKey")
    if public_key:
        reality["publicKey"] = public_key
    short_id = params.get("sid") or params.get("shortId")
    if short_id:
        reality["shortId"] = short_id
    server_name = params.get("sni") or params.get("serverName")
    if server_name:
        reality["serverName"] = server_name
    fingerprint = params.get("fp") or params.get("fingerprint")
    if fingerprint:
        reality["fingerprint"] = fingerprint
    if params.get("spx"):
        reality["spiderX"] = params["spx"]
    return reality


def _split_url(url: str):
    """urlsplit that validates host/port; returns None on any parse failure."""
    try:
        parts = urllib.parse.urlsplit(url)
        host = parts.hostname
        port = parts.port
    except ValueError:
        return None
    if not host or port is None:
        return None
    if not validate_hostname(host) or not validate_port(port):
        return None
    return parts, host, port


def _parse_vless(url: str) -> Optional[Dict[str, Any]]:
    split = _split_url(url)
    if not split:
        return None
    parts, host, port = split

    uuid_str = urllib.parse.unquote(parts.username or "")
    if not validate_uuid(uuid_str):
        return None

    params = _parse_query(parts.query)
    network = _normalize_network(params.get("type") or params.get("network"))
    security = (params.get("security") or "none").lower()

    profile: Dict[str, Any] = {
        "protocol": "vless",
        "uuid": uuid_str.lower(),
        "address": host,
        "port": port,
        "network": network,
        "security": security,
        "encryption": params.get("encryption") or "none",
    }
    if params.get("flow"):
        profile["flow"] = params["flow"]

    transport = _transport_from_params(network, params)
    if transport:
        profile["transport"] = transport

    if security == "tls":
        tls = _tls_from_params(params)
        if tls:
            profile["tlsConfig"] = tls
    elif security == "reality":
        reality = _reality_from_params(params)
        if reality:
            profile["realityConfig"] = reality

    if parts.fragment:
        profile["name"] = urllib.parse.unquote(parts.fragment)
    return profile


def _parse_trojan(url: str) -> Optional[Dict[str, Any]]:
    split = _split_url(url)
    if not split:
        return None
    parts, host, port = split

    password = urllib.parse.unquote(parts.username or "")
    if not password:
        return None

    params = _parse_query(parts.query)
    network = _normalize_network(params.get("type") or params.get("network"))
    # Trojan is TLS-based; share links usually omit the security param.
    security = (params.get("security") or "tls").lower()

    profile: Dict[str, Any] = {
        "protocol": "trojan",
        "password": password,
        "address": host,
        "port": port,
        "network": network,
        "security": security,
    }

    transport = _transport_from_params(network, params)
    if transport:
        profile["transport"] = transport

    if security == "tls":
        tls = _tls_from_params(params)
        if tls:
            profile["tlsConfig"] = tls
    elif security == "reality":
        reality = _reality_from_params(params)
        if reality:
            profile["realityConfig"] = reality

    if parts.fragment:
        profile["name"] = urllib.parse.unquote(parts.fragment)
    return profile


def _ss_credentials(parts) -> Optional[Tuple[str, str]]:
    """Resolve SIP002 userinfo into (method, password)."""
    if parts.password is not None:
        # Plain percent-encoded "method:password" (Shadowsocks 2022 style).
        return (
            urllib.parse.unquote(parts.username or ""),
            urllib.parse.unquote(parts.password),
        )
    decoded = _decode_base64(urllib.parse.unquote(parts.username or ""))
    if decoded and ":" in decoded:
        method, password = decoded.split(":", 1)
        return method, password
    return None


def _parse_ss(url: str) -> Optional[Dict[str, Any]]:
    body = url[len("ss://"):]
    fragment = ""
    if "#" in body:
        body, fragment = body.split("#", 1)
    name = urllib.parse.unquote(fragment) if fragment else None

    if "@" in body:
        # SIP002: ss://userinfo@host:port[/][?plugin=...]
        split = _split_url("ss://" + body)
        if not split:
            return None
        parts, host, port = split
        credentials = _ss_credentials(parts)
        if not credentials:
            return None
        method, password = credentials
        params = _parse_query(parts.query)
        if params.get("plugin"):
            # SIP003 plugins (obfs, v2ray-plugin) are not supported by xray-core.
            return None
    else:
        # Legacy: ss://base64(method:password@host:port)
        decoded = _decode_base64(body)
        if not decoded or "@" not in decoded or ":" not in decoded:
            return None
        userinfo, hostport = decoded.rsplit("@", 1)
        if ":" not in userinfo or ":" not in hostport:
            return None
        method, password = userinfo.split(":", 1)
        host, port_str = hostport.rsplit(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            return None
        if not validate_hostname(host) or not validate_port(port):
            return None

    if not method or not password:
        return None

    profile: Dict[str, Any] = {
        "protocol": "shadowsocks",
        "method": method.lower(),
        "password": password,
        "address": host,
        "port": port,
        "network": "tcp",
        "security": "none",
    }
    if name:
        profile["name"] = name
    return profile


def _socks_credentials(parts) -> Tuple[str, str]:
    """
    Resolve socks userinfo into (username, password); ("", "") when absent.

    Accepts the plain ``user:pass@`` form and the v2rayN-style
    ``base64(user:pass)@`` form.
    """
    if parts.password is not None:
        return (
            urllib.parse.unquote(parts.username or ""),
            urllib.parse.unquote(parts.password),
        )
    username = urllib.parse.unquote(parts.username or "")
    if not username:
        return "", ""
    decoded = _decode_base64(username)
    if decoded and ":" in decoded:
        user, password = decoded.split(":", 1)
        return user, password
    # Username with no password — valid for servers that only check the user.
    return username, ""


def _parse_socks(url: str) -> Optional[Dict[str, Any]]:
    """
    Parse a socks:// (socks5://) link pointing at a user's own SOCKS5 proxy.

    Plain SOCKS5 carries no transport encryption, so the profile is always
    tcp/none — any query parameters are ignored rather than silently
    promising TLS the protocol does not provide.
    """
    split = _split_url(url)
    if not split:
        return None
    parts, host, port = split

    username, password = _socks_credentials(parts)

    profile: Dict[str, Any] = {
        "protocol": "socks",
        "address": host,
        "port": port,
        "network": "tcp",
        "security": "none",
    }
    if username:
        profile["username"] = username
        if password:
            profile["password"] = password
    if parts.fragment:
        profile["name"] = urllib.parse.unquote(parts.fragment)
    return profile


def _parse_vmess(url: str) -> Optional[Dict[str, Any]]:
    decoded = _decode_base64(url[len("vmess://"):])
    if not decoded:
        return None
    try:
        data = json.loads(decoded)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None

    uuid_str = str(data.get("id") or "")
    if not validate_uuid(uuid_str):
        return None

    host = str(data.get("add") or "")
    if not validate_hostname(host):
        return None
    try:
        port = int(data.get("port") or 0)
    except (ValueError, TypeError):
        return None
    if not validate_port(port):
        return None

    network = _normalize_network(str(data.get("net") or "tcp"))
    tls_field = str(data.get("tls") or "").lower()
    security = "tls" if tls_field in ("tls", "1", "true") else "none"

    try:
        alter_id = int(data.get("aid") or 0)
    except (ValueError, TypeError):
        alter_id = 0

    profile: Dict[str, Any] = {
        "protocol": "vmess",
        "uuid": uuid_str.lower(),
        "address": host,
        "port": port,
        "network": network,
        "security": security,
        "alterId": alter_id,
        "vmessSecurity": str(data.get("scy") or "auto"),
    }

    # v2rayN-style JSON carries transport fields at the top level.
    params: Dict[str, str] = {}
    if data.get("path"):
        params["path"] = str(data["path"])
    if data.get("host"):
        params["host"] = str(data["host"])
    if data.get("type") and str(data["type"]) != "none":
        params["headerType"] = str(data["type"])
    if network == "grpc" and data.get("path"):
        params["serviceName"] = str(data["path"])
    transport = _transport_from_params(network, params)
    if transport:
        profile["transport"] = transport

    if security == "tls":
        tls: Dict[str, Any] = {}
        if data.get("sni"):
            tls["serverName"] = str(data["sni"])
        if data.get("alpn"):
            alpn = [a.strip() for a in str(data["alpn"]).split(",") if a.strip()]
            if alpn:
                tls["alpn"] = alpn
        if data.get("fp"):
            tls["fingerprint"] = str(data["fp"])
        if tls:
            profile["tlsConfig"] = tls

    if data.get("ps"):
        profile["name"] = str(data["ps"])
    return profile


def _parse_hysteria2(url: str) -> Optional[Dict[str, Any]]:
    split = _split_url(url)
    if not split:
        return None
    parts, host, port = split

    # Auth is the userinfo (password) — optional in some panels.
    auth = urllib.parse.unquote(parts.username or "")
    if parts.password:
        auth = f"{auth}:{urllib.parse.unquote(parts.password)}"

    params = _parse_query(parts.query)
    profile: Dict[str, Any] = {
        "protocol": "hysteria2",
        "core": "sing-box",
        "password": auth,
        "address": host,
        "port": port,
        "network": "udp",
        "security": "tls",
    }
    tls: Dict[str, Any] = {}
    if params.get("sni"):
        tls["serverName"] = params["sni"]
    if _is_truthy(params.get("insecure")) or _is_truthy(params.get("allowInsecure")):
        tls["allowInsecure"] = True
    if tls:
        profile["tlsConfig"] = tls
    if params.get("obfs"):
        profile["obfs"] = params["obfs"]
        if params.get("obfs-password"):
            profile["obfsPassword"] = params["obfs-password"]
    if parts.fragment:
        profile["name"] = urllib.parse.unquote(parts.fragment)
    return profile


def _parse_tuic(url: str) -> Optional[Dict[str, Any]]:
    split = _split_url(url)
    if not split:
        return None
    parts, host, port = split

    uuid_str = urllib.parse.unquote(parts.username or "")
    if not validate_uuid(uuid_str):
        return None
    password = urllib.parse.unquote(parts.password) if parts.password else ""

    params = _parse_query(parts.query)
    profile: Dict[str, Any] = {
        "protocol": "tuic",
        "core": "sing-box",
        "uuid": uuid_str.lower(),
        "password": password,
        "address": host,
        "port": port,
        "network": "udp",
        "security": "tls",
    }
    if params.get("congestion_control"):
        profile["congestionControl"] = params["congestion_control"]
    if params.get("udp_relay_mode"):
        profile["udpRelayMode"] = params["udp_relay_mode"]
    tls: Dict[str, Any] = {}
    if params.get("sni"):
        tls["serverName"] = params["sni"]
    if params.get("alpn"):
        alpn = [a.strip() for a in params["alpn"].split(",") if a.strip()]
        if alpn:
            tls["alpn"] = alpn
    if _is_truthy(params.get("allow_insecure")) or _is_truthy(params.get("insecure")):
        tls["allowInsecure"] = True
    if tls:
        profile["tlsConfig"] = tls
    if parts.fragment:
        profile["name"] = urllib.parse.unquote(parts.fragment)
    return profile


def parse_share_link(url: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single share link into a profile dictionary.

    Supported schemes: vless://, vmess://, trojan://, ss://,
    socks:// (socks5://), hysteria2:// (hy2://), tuic://.
    Each profile carries a "core" field
    ("xray" or "sing-box") naming the core that runs it.

    Returns:
        Profile dictionary, or None if the link is invalid/unsupported.
    """
    if not url or not isinstance(url, str):
        return None
    url = url.strip()
    lowered = url.lower()

    if lowered.startswith("vless://"):
        profile = _parse_vless(url)
    elif lowered.startswith("vmess://"):
        profile = _parse_vmess(url)
    elif lowered.startswith("trojan://"):
        profile = _parse_trojan(url)
    elif lowered.startswith("ss://"):
        profile = _parse_ss(url)
    elif lowered.startswith("socks://") or lowered.startswith("socks5://"):
        profile = _parse_socks(url)
    elif lowered.startswith("hysteria2://") or lowered.startswith("hy2://"):
        return _parse_hysteria2(url)
    elif lowered.startswith("tuic://"):
        return _parse_tuic(url)
    else:
        return None

    # Tag the xray-core protocols with their core for uniform dispatch.
    if profile is not None and "core" not in profile:
        profile["core"] = "xray"
    return profile


def parse_subscription(text: str) -> List[Dict[str, Any]]:
    """
    Parse a base64 subscription payload into a list of profiles.

    Supports the de facto standard (base64 of newline-delimited share links)
    and the legacy format (base64 of a JSON array of links).
    """
    decoded = _decode_base64(text)
    if decoded is None:
        return []

    # Legacy: JSON array of share links.
    try:
        items = json.loads(decoded)
        if isinstance(items, list):
            profiles = []
            for item in items:
                if isinstance(item, str):
                    parsed = parse_share_link(item)
                    if parsed:
                        profiles.append(parsed)
            return profiles
    except json.JSONDecodeError:
        pass

    # Standard: newline-delimited share links.
    if "://" in decoded:
        profiles = []
        for line in decoded.splitlines():
            parsed = parse_share_link(line.strip())
            if parsed:
                profiles.append(parsed)
        return profiles

    return []


def parse_subscription_content(text: str) -> List[Dict[str, Any]]:
    """
    Parse a fetched subscription body into profiles.

    Handles both the de facto standard (base64 of newline-delimited links,
    via parse_subscription) and servers that return plain-text link lists.
    """
    if not text or not isinstance(text, str):
        return []

    profiles = parse_subscription(text)
    if profiles:
        return profiles

    if "://" in text:
        profiles = []
        for line in text.splitlines():
            parsed = parse_share_link(line.strip())
            if parsed:
                profiles.append(parsed)
        return profiles

    return []


def validate_share_link(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a share link (single node or base64 subscription).

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "Invalid URL format"

    url = url.strip()

    if parse_share_link(url):
        return True, None

    if parse_subscription(url):
        return True, None

    if "://" in url:
        scheme = url.split("://", 1)[0].lower()
        if scheme not in SUPPORTED_SCHEMES:
            return (
                False,
                f"Unsupported protocol '{scheme}'. "
                "Supported: vless, vmess, trojan, ss, socks",
            )

    return (
        False,
        "Invalid share link. Expected vless://, vmess://, trojan://, ss://, "
        "socks://, a subscription URL (http(s)://) or base64 subscription content",
    )


def build_profile_config(
    parsed: Dict[str, Any], source_url: str, config_type: str
) -> Dict[str, Any]:
    """
    Build the stored profile config from a parsed share link.

    Args:
        parsed: Profile dictionary from parse_share_link/parse_subscription
        source_url: Original source URL
        config_type: 'single' or 'subscription'

    Returns:
        Complete profile dictionary ready for SettingsManager.
    """
    import time

    config = dict(parsed)
    config["sourceUrl"] = source_url
    config["configType"] = config_type
    config["importedAt"] = int(time.time())
    config["isValid"] = True
    return config
