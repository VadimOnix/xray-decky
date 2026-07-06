"""
Export stored profiles back into share links.

The inverse of ``config_parser.parse_share_link``: a stored profile becomes a
standard ``vless://`` / ``vmess://`` / ``trojan://`` / ``ss://`` /
``hysteria2://`` / ``tuic://`` link, so servers can be moved to another client
or backed up. Round-trip tests (profile → link → parse → same profile) keep
this in lockstep with the parser.

Unlike the admin panel's list view — which redacts credentials — an export
necessarily contains them (a share link is the credential). It is therefore
only produced on an explicit, token-guarded request, never in passive display.
"""

import base64
import json
import urllib.parse
from typing import Any, Dict, List, Optional


def _q(value: Any) -> str:
    """Percent-encode a single URL component."""
    return urllib.parse.quote(str(value), safe="")


def _frag(profile: Dict[str, Any]) -> str:
    name = profile.get("name")
    return f"#{_q(name)}" if name else ""


def _transport_query(profile: Dict[str, Any]) -> Dict[str, str]:
    """Rebuild transport query params from a profile's transport block."""
    query: Dict[str, str] = {}
    network = profile.get("network", "tcp")
    transport = profile.get("transport") or {}
    if not isinstance(transport, dict):
        return query
    if network in ("ws", "httpupgrade", "xhttp"):
        if transport.get("path"):
            query["path"] = str(transport["path"])
        if transport.get("host"):
            query["host"] = str(transport["host"])
        if network == "xhttp" and transport.get("mode"):
            query["mode"] = str(transport["mode"])
    elif network == "grpc":
        if transport.get("serviceName"):
            query["serviceName"] = str(transport["serviceName"])
        if transport.get("authority"):
            query["authority"] = str(transport["authority"])
        if transport.get("multiMode"):
            query["mode"] = "multi"
    elif network == "kcp":
        if transport.get("headerType"):
            query["headerType"] = str(transport["headerType"])
        if transport.get("seed"):
            query["seed"] = str(transport["seed"])
    elif network == "tcp":
        if transport.get("headerType"):
            query["headerType"] = str(transport["headerType"])
            if transport.get("host"):
                query["host"] = str(transport["host"])
            if transport.get("path"):
                query["path"] = str(transport["path"])
    return query


def _tls_query(profile: Dict[str, Any]) -> Dict[str, str]:
    query: Dict[str, str] = {}
    tls = profile.get("tlsConfig") or {}
    if not isinstance(tls, dict):
        return query
    if tls.get("serverName"):
        query["sni"] = str(tls["serverName"])
    alpn = tls.get("alpn")
    if isinstance(alpn, list) and alpn:
        query["alpn"] = ",".join(str(a) for a in alpn)
    if tls.get("fingerprint"):
        query["fp"] = str(tls["fingerprint"])
    if tls.get("allowInsecure"):
        query["allowInsecure"] = "1"
    return query


def _reality_query(profile: Dict[str, Any]) -> Dict[str, str]:
    query: Dict[str, str] = {}
    reality = profile.get("realityConfig") or {}
    if not isinstance(reality, dict):
        return query
    if reality.get("publicKey"):
        query["pbk"] = str(reality["publicKey"])
    if reality.get("shortId"):
        query["sid"] = str(reality["shortId"])
    if reality.get("serverName"):
        query["sni"] = str(reality["serverName"])
    if reality.get("fingerprint"):
        query["fp"] = str(reality["fingerprint"])
    if reality.get("spiderX"):
        query["spx"] = str(reality["spiderX"])
    return query


def _endpoint(profile: Dict[str, Any]):
    address = profile.get("address")
    port = profile.get("port")
    if not address or port is None:
        return None
    return str(address), port


def _encode_query(query: Dict[str, str]) -> str:
    return urllib.parse.urlencode({k: v for k, v in query.items() if v})


def _vless_link(profile: Dict[str, Any]) -> Optional[str]:
    endpoint = _endpoint(profile)
    uuid = profile.get("uuid")
    if not endpoint or not uuid:
        return None
    host, port = endpoint
    network = profile.get("network", "tcp")
    security = profile.get("security", "none")
    query: Dict[str, str] = {"type": network, "security": security}
    encryption = profile.get("encryption")
    if encryption and encryption != "none":
        query["encryption"] = str(encryption)
    if profile.get("flow"):
        query["flow"] = str(profile["flow"])
    query.update(_transport_query(profile))
    if security == "tls":
        query.update(_tls_query(profile))
    elif security == "reality":
        query.update(_reality_query(profile))
    return f"vless://{_q(uuid)}@{host}:{port}?{_encode_query(query)}{_frag(profile)}"


def _trojan_link(profile: Dict[str, Any]) -> Optional[str]:
    endpoint = _endpoint(profile)
    password = profile.get("password")
    if not endpoint or not password:
        return None
    host, port = endpoint
    security = profile.get("security", "tls")
    query: Dict[str, str] = {"type": profile.get("network", "tcp"), "security": security}
    query.update(_transport_query(profile))
    if security == "tls":
        query.update(_tls_query(profile))
    elif security == "reality":
        query.update(_reality_query(profile))
    return f"trojan://{_q(password)}@{host}:{port}?{_encode_query(query)}{_frag(profile)}"


def _shadowsocks_link(profile: Dict[str, Any]) -> Optional[str]:
    endpoint = _endpoint(profile)
    method = profile.get("method")
    password = profile.get("password")
    if not endpoint or not method or password is None:
        return None
    host, port = endpoint
    userinfo = f"{_q(method)}:{_q(password)}"
    return f"ss://{userinfo}@{host}:{port}{_frag(profile)}"


def _vmess_link(profile: Dict[str, Any]) -> Optional[str]:
    endpoint = _endpoint(profile)
    uuid = profile.get("uuid")
    if not endpoint or not uuid:
        return None
    host, port = endpoint
    network = profile.get("network", "tcp")
    transport = profile.get("transport") or {}
    tls = profile.get("tlsConfig") or {}
    security = profile.get("security", "none")
    vmess: Dict[str, Any] = {
        "v": "2",
        "ps": str(profile.get("name") or ""),
        "add": host,
        "port": str(port),
        "id": str(uuid),
        "aid": str(profile.get("alterId") or 0),
        "scy": str(profile.get("vmessSecurity") or "auto"),
        "net": network,
        "type": str(transport.get("headerType") or "none"),
        "host": str(transport.get("host") or ""),
        "path": str(transport.get("path") or transport.get("serviceName") or ""),
        "tls": "tls" if security == "tls" else "",
    }
    if isinstance(tls, dict):
        if tls.get("serverName"):
            vmess["sni"] = str(tls["serverName"])
        if tls.get("fingerprint"):
            vmess["fp"] = str(tls["fingerprint"])
        alpn = tls.get("alpn")
        if isinstance(alpn, list) and alpn:
            vmess["alpn"] = ",".join(str(a) for a in alpn)
    encoded = base64.b64encode(
        json.dumps(vmess, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    return f"vmess://{encoded}"


def _hysteria2_link(profile: Dict[str, Any]) -> Optional[str]:
    endpoint = _endpoint(profile)
    if not endpoint:
        return None
    host, port = endpoint
    password = profile.get("password") or ""
    query: Dict[str, str] = {}
    tls = profile.get("tlsConfig") or {}
    if isinstance(tls, dict):
        if tls.get("serverName"):
            query["sni"] = str(tls["serverName"])
        if tls.get("allowInsecure"):
            query["insecure"] = "1"
    if profile.get("obfs"):
        query["obfs"] = str(profile["obfs"])
        if profile.get("obfsPassword"):
            query["obfs-password"] = str(profile["obfsPassword"])
    encoded = _encode_query(query)
    suffix = f"?{encoded}" if encoded else ""
    return f"hysteria2://{_q(password)}@{host}:{port}{suffix}{_frag(profile)}"


def _tuic_link(profile: Dict[str, Any]) -> Optional[str]:
    endpoint = _endpoint(profile)
    uuid = profile.get("uuid")
    if not endpoint or not uuid:
        return None
    host, port = endpoint
    password = profile.get("password") or ""
    query: Dict[str, str] = {}
    if profile.get("congestionControl"):
        query["congestion_control"] = str(profile["congestionControl"])
    if profile.get("udpRelayMode"):
        query["udp_relay_mode"] = str(profile["udpRelayMode"])
    tls = profile.get("tlsConfig") or {}
    if isinstance(tls, dict):
        if tls.get("serverName"):
            query["sni"] = str(tls["serverName"])
        alpn = tls.get("alpn")
        if isinstance(alpn, list) and alpn:
            query["alpn"] = ",".join(str(a) for a in alpn)
        if tls.get("allowInsecure"):
            query["allow_insecure"] = "1"
    encoded = _encode_query(query)
    suffix = f"?{encoded}" if encoded else ""
    return f"tuic://{_q(uuid)}:{_q(password)}@{host}:{port}{suffix}{_frag(profile)}"


_BUILDERS = {
    "vless": _vless_link,
    "vmess": _vmess_link,
    "trojan": _trojan_link,
    "shadowsocks": _shadowsocks_link,
    "hysteria2": _hysteria2_link,
    "tuic": _tuic_link,
}


def profile_to_share_link(profile: Dict[str, Any]) -> Optional[str]:
    """Serialize a stored profile back into a share link, or None if unsupported."""
    if not isinstance(profile, dict):
        return None
    builder = _BUILDERS.get(profile.get("protocol"))
    if not builder:
        return None
    return builder(profile)


def export_profiles(profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Export a list of profiles as share links plus a base64 subscription blob.

    Returns:
        {"links": [{"id", "name", "protocol", "link"} ...],
         "subscription": base64 of the newline-joined links (standard format),
         "count": number of exported links}
    """
    links: List[Dict[str, Any]] = []
    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        link = profile_to_share_link(profile)
        if not link:
            continue
        links.append(
            {
                "id": profile.get("id"),
                "name": profile.get("name") or profile.get("address"),
                "protocol": profile.get("protocol"),
                "link": link,
            }
        )
    joined = "\n".join(item["link"] for item in links)
    subscription = (
        base64.b64encode(joined.encode("utf-8")).decode("ascii") if joined else ""
    )
    return {"links": links, "subscription": subscription, "count": len(links)}
