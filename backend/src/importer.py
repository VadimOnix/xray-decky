"""
Shared import flow for share links and subscriptions.

Used by both the plugin RPC (main.py) and the web import/admin endpoints,
so the behavior can't drift between entry points:

- http(s):// link  -> fetched as a subscription URL; all nodes stored,
                      subscription metadata recorded for later refresh
- vless://... etc. -> appended to the profile list and made active
- base64 payload   -> treated as pasted subscription content (all nodes)
"""

import time
from typing import Any, Dict, NamedTuple, Optional

import aiohttp

from .config_parser import (
    build_profile_config,
    parse_share_link,
    parse_subscription,
    parse_subscription_content,
    validate_share_link,
)
from .profile_store import ProfileStore
from .singbox_import import looks_like_singbox_config, parse_singbox_config

FETCH_TIMEOUT = 15.0
_USER_AGENT = "xray-decky (Steam Deck; +https://github.com/VadimOnix/xray-decky)"
# Subscription bodies are tiny (a few KB of links); cap reads so a hostile
# or misconfigured server can't balloon memory.
_MAX_BODY_BYTES = 2 * 1024 * 1024
# De facto standard header carrying the account's quota/expiry, emitted by
# most subscription panels (v2board, marzban, sspanel, …).
_USERINFO_HEADER = "Subscription-Userinfo"
_USERINFO_KEYS = ("upload", "download", "total", "expire")


class SubscriptionResponse(NamedTuple):
    """A fetched subscription: its body and optional quota/expiry userinfo."""

    body: Optional[str]
    userinfo: Optional[Dict[str, int]]


def parse_subscription_userinfo(header: Optional[str]) -> Optional[Dict[str, int]]:
    """
    Parse a ``Subscription-Userinfo`` header into integer fields.

    The header looks like ``upload=1; download=2; total=3; expire=456`` (bytes
    and a unix timestamp). Unknown keys and non-integer values are skipped;
    returns None when nothing usable is present.
    """
    if not header or not isinstance(header, str):
        return None
    info: Dict[str, int] = {}
    for part in header.split(";"):
        key, sep, value = part.partition("=")
        if not sep:
            continue
        key = key.strip().lower()
        value = value.strip()
        if key in _USERINFO_KEYS and value:
            try:
                info[key] = int(value)
            except ValueError:
                continue
    return info or None


async def fetch_subscription(
    url: str, timeout: float = FETCH_TIMEOUT
) -> SubscriptionResponse:
    """
    Fetch a subscription URL's body and userinfo; body is None on any failure.

    Fetching a user-provided URL is this feature's purpose (CodeQL flags it
    as SSRF): the URL is chosen by the device owner in the QAM or by a
    token-authenticated admin — the same trust model as every proxy client
    with subscription support. The response is never echoed back; it is
    only parsed for share links, size-capped, and restricted to http(s).
    """
    if not url.lower().startswith(("http://", "https://")):
        return SubscriptionResponse(None, None)
    try:
        client_timeout = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=client_timeout) as session:
            async with session.get(
                url, headers={"User-Agent": _USER_AGENT}
            ) as response:
                if response.status != 200:
                    return SubscriptionResponse(None, None)
                body = await response.content.read(_MAX_BODY_BYTES + 1)
                if len(body) > _MAX_BODY_BYTES:
                    return SubscriptionResponse(None, None)
                charset = response.charset or "utf-8"
                text = body.decode(charset, errors="replace")
                userinfo = parse_subscription_userinfo(
                    response.headers.get(_USERINFO_HEADER)
                )
                return SubscriptionResponse(text, userinfo)
    except Exception:
        return SubscriptionResponse(None, None)


async def import_link(store: ProfileStore, link: str) -> Dict[str, Any]:
    """
    Import a link into the profile store.

    Returns:
        {"success": bool, "error": str | None,
         "config": dict | None, "profileCount": int}
    """
    link = (link or "").strip()
    if not link:
        return {"success": False, "error": "Empty link"}

    now = int(time.time())

    if link.lower().startswith(("http://", "https://")):
        response = await fetch_subscription(link)
        if response.body is None:
            return {
                "success": False,
                "error": "Failed to fetch subscription URL (check the address "
                "and network)",
            }
        nodes = parse_subscription_content(response.body)
        if not nodes:
            return {
                "success": False,
                "error": "Subscription contains no supported share links",
            }
        configs = []
        for node in nodes:
            config = build_profile_config(node, link, "subscription")
            config["lastValidatedAt"] = now
            configs.append(config)
        store.replace_subscription_profiles(configs)
        store.set_subscription(link, len(configs), userinfo=response.userinfo)
        return {
            "success": True,
            "error": None,
            "config": configs[0],
            "profileCount": len(configs),
        }

    if looks_like_singbox_config(link):
        # A pasted sing-box JSON config: import every server outbound. Like a
        # pasted subscription, there's no URL to refresh from.
        nodes = parse_singbox_config(link)
        if not nodes:
            return {
                "success": False,
                "error": "sing-box config has no supported server outbounds",
            }
        configs = []
        for node in nodes:
            config = build_profile_config(node, "sing-box-json", "subscription")
            config["lastValidatedAt"] = now
            configs.append(config)
        store.replace_subscription_profiles(configs)
        store.clear_subscription()
        return {
            "success": True,
            "error": None,
            "config": configs[0],
            "profileCount": len(configs),
        }

    is_valid, error_msg = validate_share_link(link)
    if not is_valid:
        return {"success": False, "error": error_msg or "Invalid share link"}

    parsed = parse_share_link(link)
    if parsed:
        # Single link: append to the profile list and make it active.
        config = build_profile_config(parsed, link, "single")
        config["lastValidatedAt"] = now
        store.add(config)
        return {
            "success": True,
            "error": None,
            "config": config,
            "profileCount": len(store.list_profiles()),
        }

    # Pasted base64 subscription content: store every node. There's no URL to
    # refresh, so forget any prior subscription metadata.
    nodes = parse_subscription(link)
    if not nodes:
        return {"success": False, "error": "Failed to parse share link"}
    configs = []
    for node in nodes:
        config = build_profile_config(node, link, "subscription")
        config["lastValidatedAt"] = now
        configs.append(config)
    store.replace_subscription_profiles(configs)
    store.clear_subscription()
    return {
        "success": True,
        "error": None,
        "config": configs[0],
        "profileCount": len(configs),
    }


async def refresh_subscription(store: ProfileStore) -> Dict[str, Any]:
    """
    Re-fetch the stored subscription URL and replace the profile list.
    The active server survives the refresh when it's still in the list
    (matched by protocol/address/port).
    """
    subscription = store.get_subscription()
    if not subscription or not subscription.get("url"):
        return {"success": False, "error": "No subscription to refresh"}
    return await import_link(store, subscription["url"])
