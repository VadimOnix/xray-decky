"""
Import proxy servers from a sing-box JSON config.

sing-box GUIs (SFI/SFA, NekoBox-style tools) and many panels export a full
sing-box config, or just an ``outbounds`` array. Rather than duplicate all the
transport/TLS/REALITY handling, we turn each server-type outbound back into a
standard share link and feed it through the existing, well-tested share-link
parser. One parsing path, no drift.

Only *server* outbounds are imported; structural ones (``direct``, ``block``,
``dns``, ``selector``, ``urltest``, …) are skipped silently.
"""

import base64
import json
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

from .config_parser import parse_share_link

# Outbound "type" values we know how to turn into share links.
_SERVER_TYPES = {"vless", "vmess", "trojan", "shadowsocks", "hysteria2", "tuic"}


def _q(value: Any) -> str:
    """Percent-encode a single URL component."""
    return urllib.parse.quote(str(value), safe="")


def _frag(tag: Any) -> str:
    """Build the ``#name`` fragment from an outbound tag, if any."""
    return f"#{_q(tag)}" if tag else ""


def _outbounds(data: Any) -> List[Dict[str, Any]]:
    """Return outbound objects from a full config or a bare outbounds array."""
    if isinstance(data, list):
        return [o for o in data if isinstance(o, dict)]
    if isinstance(data, dict):
        outbounds = data.get("outbounds")
        if isinstance(outbounds, list):
            return [o for o in outbounds if isinstance(o, dict)]
    return []


def _tls_params(outbound: Dict[str, Any]) -> Dict[str, str]:
    """Map a sing-box ``tls`` block to share-link query params."""
    params: Dict[str, str] = {}
    tls = outbound.get("tls")
    if not isinstance(tls, dict) or not tls.get("enabled"):
        return params
    if tls.get("server_name"):
        params["sni"] = str(tls["server_name"])
    alpn = tls.get("alpn")
    if isinstance(alpn, list) and alpn:
        params["alpn"] = ",".join(str(a) for a in alpn)
    elif isinstance(alpn, str) and alpn:
        params["alpn"] = alpn
    utls = tls.get("utls")
    if isinstance(utls, dict) and utls.get("fingerprint"):
        params["fp"] = str(utls["fingerprint"])
    if tls.get("insecure"):
        params["insecure"] = "1"
    reality = tls.get("reality")
    if isinstance(reality, dict) and reality.get("enabled"):
        if reality.get("public_key"):
            params["pbk"] = str(reality["public_key"])
        if reality.get("short_id"):
            params["sid"] = str(reality["short_id"])
    return params


def _tls_security(outbound: Dict[str, Any]) -> str:
    """Return the share-link ``security`` value for an outbound's tls block."""
    tls = outbound.get("tls")
    if not isinstance(tls, dict) or not tls.get("enabled"):
        return "none"
    reality = tls.get("reality")
    if isinstance(reality, dict) and reality.get("enabled"):
        return "reality"
    return "tls"


def _transport(outbound: Dict[str, Any]) -> Tuple[str, Dict[str, str]]:
    """Map a sing-box ``transport`` block to (network, query params)."""
    params: Dict[str, str] = {}
    transport = outbound.get("transport")
    if not isinstance(transport, dict):
        return "tcp", params
    ttype = transport.get("type")
    if ttype in ("ws", "httpupgrade"):
        if transport.get("path"):
            params["path"] = str(transport["path"])
        headers = transport.get("headers")
        if isinstance(headers, dict):
            host = headers.get("Host") or headers.get("host")
            if isinstance(host, list) and host:
                host = host[0]
            if host:
                params["host"] = str(host)
        return ttype, params
    if ttype == "grpc":
        if transport.get("service_name"):
            params["serviceName"] = str(transport["service_name"])
        return "grpc", params
    # Unknown/omitted transport → plain tcp (sing-box's own default).
    return "tcp", params


def _endpoint(outbound: Dict[str, Any]):
    """Return (server, port) if both are present, else None."""
    server = outbound.get("server")
    port = outbound.get("server_port")
    if not server or port is None:
        return None
    return str(server), port


def _vless_link(outbound: Dict[str, Any]) -> Optional[str]:
    endpoint = _endpoint(outbound)
    uuid = outbound.get("uuid")
    if not endpoint or not uuid:
        return None
    server, port = endpoint
    network, params = _transport(outbound)
    params.update(_tls_params(outbound))
    params["type"] = network
    params["security"] = _tls_security(outbound)
    if outbound.get("flow"):
        params["flow"] = str(outbound["flow"])
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v})
    return f"vless://{_q(uuid)}@{server}:{port}?{query}{_frag(outbound.get('tag'))}"


def _trojan_link(outbound: Dict[str, Any]) -> Optional[str]:
    endpoint = _endpoint(outbound)
    password = outbound.get("password")
    if not endpoint or not password:
        return None
    server, port = endpoint
    network, params = _transport(outbound)
    params.update(_tls_params(outbound))
    params["type"] = network
    params["security"] = _tls_security(outbound) or "tls"
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v})
    return f"trojan://{_q(password)}@{server}:{port}?{query}{_frag(outbound.get('tag'))}"


def _shadowsocks_link(outbound: Dict[str, Any]) -> Optional[str]:
    endpoint = _endpoint(outbound)
    method = outbound.get("method")
    password = outbound.get("password")
    if not endpoint or not method or password is None:
        return None
    server, port = endpoint
    # SIP002 "method:password" userinfo form (parsed directly, no base64).
    userinfo = f"{_q(method)}:{_q(password)}"
    return f"ss://{userinfo}@{server}:{port}{_frag(outbound.get('tag'))}"


def _vmess_link(outbound: Dict[str, Any]) -> Optional[str]:
    endpoint = _endpoint(outbound)
    uuid = outbound.get("uuid")
    if not endpoint or not uuid:
        return None
    server, port = endpoint
    network, params = _transport(outbound)
    tls = outbound.get("tls")
    tls_on = isinstance(tls, dict) and bool(tls.get("enabled"))
    vmess: Dict[str, Any] = {
        "v": "2",
        "ps": str(outbound.get("tag") or ""),
        "add": server,
        "port": str(port),
        "id": str(uuid),
        "aid": str(outbound.get("alter_id") or 0),
        "scy": str(outbound.get("security") or "auto"),
        "net": network,
        "type": "none",
        "host": params.get("host", ""),
        "path": params.get("path") or params.get("serviceName", ""),
        "tls": "tls" if tls_on else "",
    }
    if tls_on and isinstance(tls, dict) and tls.get("server_name"):
        vmess["sni"] = str(tls["server_name"])
    encoded = base64.b64encode(
        json.dumps(vmess, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    return f"vmess://{encoded}"


def _hysteria2_link(outbound: Dict[str, Any]) -> Optional[str]:
    endpoint = _endpoint(outbound)
    if not endpoint:
        return None
    server, port = endpoint
    password = outbound.get("password") or ""
    params: Dict[str, str] = _tls_params(outbound)
    obfs = outbound.get("obfs")
    if isinstance(obfs, dict) and obfs.get("type"):
        params["obfs"] = str(obfs["type"])
        if obfs.get("password"):
            params["obfs-password"] = str(obfs["password"])
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v})
    suffix = f"?{query}" if query else ""
    return f"hysteria2://{_q(password)}@{server}:{port}{suffix}{_frag(outbound.get('tag'))}"


def _tuic_link(outbound: Dict[str, Any]) -> Optional[str]:
    endpoint = _endpoint(outbound)
    uuid = outbound.get("uuid")
    if not endpoint or not uuid:
        return None
    server, port = endpoint
    password = outbound.get("password") or ""
    params: Dict[str, str] = _tls_params(outbound)
    if outbound.get("congestion_control"):
        params["congestion_control"] = str(outbound["congestion_control"])
    if outbound.get("udp_relay_mode"):
        params["udp_relay_mode"] = str(outbound["udp_relay_mode"])
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v})
    suffix = f"?{query}" if query else ""
    return (
        f"tuic://{_q(uuid)}:{_q(password)}@{server}:{port}"
        f"{suffix}{_frag(outbound.get('tag'))}"
    )


_BUILDERS = {
    "vless": _vless_link,
    "vmess": _vmess_link,
    "trojan": _trojan_link,
    "shadowsocks": _shadowsocks_link,
    "hysteria2": _hysteria2_link,
    "tuic": _tuic_link,
}


def looks_like_singbox_config(text: str) -> bool:
    """Cheap check: does this look like a JSON object/array (a sing-box config)?"""
    if not text or not isinstance(text, str):
        return False
    return text.lstrip()[:1] in ("{", "[")


def singbox_config_to_links(text: str) -> List[str]:
    """Convert a sing-box config's server outbounds into share links."""
    if not looks_like_singbox_config(text):
        return []
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return []
    links: List[str] = []
    for outbound in _outbounds(data):
        builder = _BUILDERS.get(outbound.get("type"))
        if not builder:
            continue
        link = builder(outbound)
        if link:
            links.append(link)
    return links


def parse_singbox_config(text: str) -> List[Dict[str, Any]]:
    """
    Parse a sing-box JSON config into a list of profile dictionaries.

    Server outbounds are converted to share links and run through
    ``parse_share_link``; anything that fails to parse is dropped. Returns an
    empty list when the text isn't a sing-box config or has no usable servers.
    """
    profiles: List[Dict[str, Any]] = []
    for link in singbox_config_to_links(text):
        parsed = parse_share_link(link)
        if parsed:
            profiles.append(parsed)
    return profiles
