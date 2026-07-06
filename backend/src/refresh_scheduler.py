"""
Scheduled subscription refresh — pure scheduling decisions.

The plugin runs a slow background tick (see main.py); this module holds the
side-effect-free "is a refresh due yet?" logic so it can be unit-tested with an
injected clock. A refresh is due only when the user has opted in (a positive
interval) for a URL-backed subscription whose last update is older than the
interval. Default state (no interval) means auto-refresh is off — zero change
to existing behavior.
"""

from typing import Any, Dict, Optional

SECONDS_PER_HOUR = 3600


def refresh_interval_hours(subscription: Optional[Dict[str, Any]]) -> int:
    """The configured auto-refresh interval in hours (0 = disabled)."""
    if not isinstance(subscription, dict):
        return 0
    try:
        return max(0, int(subscription.get("refreshIntervalHours", 0) or 0))
    except (ValueError, TypeError):
        return 0


def is_refresh_due(subscription: Optional[Dict[str, Any]], now: float) -> bool:
    """
    True when a URL subscription's auto-refresh interval has elapsed.

    Requires a stored refreshable subscription (a ``url``), a positive
    interval, and ``now`` at least one interval past ``updatedAt``. A missing
    or non-numeric ``updatedAt`` is treated as "never updated" → due.
    """
    if not isinstance(subscription, dict) or not subscription.get("url"):
        return False
    hours = refresh_interval_hours(subscription)
    if hours <= 0:
        return False
    try:
        updated_at = float(subscription.get("updatedAt") or 0)
    except (ValueError, TypeError):
        updated_at = 0.0
    return now - updated_at >= hours * SECONDS_PER_HOUR
