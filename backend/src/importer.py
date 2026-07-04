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
from typing import Any, Dict, Optional

import aiohttp

from .config_parser import (
    build_profile_config,
    parse_share_link,
    parse_subscription,
    parse_subscription_content,
    validate_share_link,
)
from .profile_store import ProfileStore

FETCH_TIMEOUT = 15.0
_USER_AGENT = "xray-decky (Steam Deck; +https://github.com/VadimOnix/xray-decky)"


async def fetch_subscription(url: str, timeout: float = FETCH_TIMEOUT) -> Optional[str]:
    """Fetch a subscription URL's body; None on any network/HTTP failure."""
    try:
        client_timeout = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=client_timeout) as session:
            async with session.get(
                url, headers={"User-Agent": _USER_AGENT}
            ) as response:
                if response.status != 200:
                    return None
                return await response.text()
    except Exception:
        return None


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
        body = await fetch_subscription(link)
        if body is None:
            return {
                "success": False,
                "error": "Failed to fetch subscription URL (check the address "
                "and network)",
            }
        nodes = parse_subscription_content(body)
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
        store.replace_all(configs)
        store.set_subscription(link, len(configs))
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

    # Pasted base64 subscription content: store every node.
    nodes = parse_subscription(link)
    if not nodes:
        return {"success": False, "error": "Failed to parse share link"}
    configs = []
    for node in nodes:
        config = build_profile_config(node, link, "subscription")
        config["lastValidatedAt"] = now
        configs.append(config)
    store.replace_all(configs)
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
