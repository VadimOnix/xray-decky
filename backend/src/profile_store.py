"""
Multi-server profile store (settings schema v2).

Profiles live under the "profiles" settings key:

    {
      "version": 2,
      "activeId": "ab12cd34" | None,
      "items": [ { "id": "...", ...profile fields... }, ... ]
    }

The active profile is mirrored into the legacy "vlessConfig" key on every
mutation, so the connection path and older frontends keep working unchanged.
A legacy single "vlessConfig" is migrated into the list on first load.
"""

import time
import uuid
from typing import Any, Dict, List, Optional

PROFILES_KEY = "profiles"
LEGACY_KEY = "vlessConfig"
SCHEMA_VERSION = 2


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


class ProfileStore:
    """CRUD + active-profile selection over SettingsManager."""

    def __init__(self, settings) -> None:
        self._settings = settings

    # ----- persistence helpers -----

    def _load(self) -> Dict[str, Any]:
        data = self._settings.getSetting(PROFILES_KEY, None)
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            return data
        return self._migrate_legacy()

    def _migrate_legacy(self) -> Dict[str, Any]:
        """Build schema v2 from a legacy single vlessConfig (or empty)."""
        data: Dict[str, Any] = {
            "version": SCHEMA_VERSION,
            "activeId": None,
            "items": [],
        }
        legacy = self._settings.getSetting(LEGACY_KEY, None)
        if isinstance(legacy, dict) and legacy.get("address"):
            profile = dict(legacy)
            profile["id"] = _new_id()
            data["items"] = [profile]
            data["activeId"] = profile["id"]
        self._save(data)
        return data

    def _save(self, data: Dict[str, Any]) -> None:
        data["version"] = SCHEMA_VERSION
        self._settings.setSetting(PROFILES_KEY, data)
        self._mirror_active(data)
        self._settings.commit()

    def _mirror_active(self, data: Dict[str, Any]) -> None:
        """Keep the legacy vlessConfig key equal to the active profile."""
        active = None
        for item in data["items"]:
            if item.get("id") == data.get("activeId"):
                active = item
                break
        if active is not None:
            mirror = dict(active)
            mirror.pop("id", None)
            self._settings.setSetting(LEGACY_KEY, mirror)
        else:
            self._settings.setSetting(LEGACY_KEY, None)

    # ----- public API -----

    def list_profiles(self) -> List[Dict[str, Any]]:
        return list(self._load()["items"])

    def get_active_id(self) -> Optional[str]:
        return self._load().get("activeId")

    def get_active(self) -> Optional[Dict[str, Any]]:
        data = self._load()
        for item in data["items"]:
            if item.get("id") == data.get("activeId"):
                return dict(item)
        return None

    def get(self, profile_id: str) -> Optional[Dict[str, Any]]:
        for item in self._load()["items"]:
            if item.get("id") == profile_id:
                return dict(item)
        return None

    def add(self, profile: Dict[str, Any], *, make_active: bool = True) -> str:
        """Append a profile; returns its id."""
        data = self._load()
        item = dict(profile)
        item["id"] = _new_id()
        data["items"].append(item)
        if make_active or data.get("activeId") is None:
            data["activeId"] = item["id"]
        self._save(data)
        return item["id"]

    def replace_all(self, profiles: List[Dict[str, Any]]) -> List[str]:
        """
        Replace the whole list (subscription import). The first profile
        becomes active; if a previously active server (same protocol,
        address and port) is still present, it stays active. Returns the
        new ids. Subscription metadata is cleared — the importer sets it
        again for URL-based subscriptions.
        """
        previous_active = self.get_active()
        data: Dict[str, Any] = {
            "version": SCHEMA_VERSION,
            "activeId": None,
            "items": [],
        }
        for profile in profiles:
            item = dict(profile)
            item["id"] = _new_id()
            data["items"].append(item)
        if data["items"]:
            data["activeId"] = data["items"][0]["id"]
            if previous_active is not None:
                key = (
                    previous_active.get("protocol"),
                    previous_active.get("address"),
                    previous_active.get("port"),
                )
                for item in data["items"]:
                    if (
                        item.get("protocol"),
                        item.get("address"),
                        item.get("port"),
                    ) == key:
                        data["activeId"] = item["id"]
                        break
        self._save(data)
        return [item["id"] for item in data["items"]]

    def set_subscription(self, url: str, node_count: int, userinfo=None) -> None:
        """Record where the current profile list came from (for refresh).

        ``userinfo`` is the optional quota/expiry dict from the subscription's
        ``Subscription-Userinfo`` header (upload/download/total/expire).
        """
        data = self._load()
        data["subscription"] = {
            "url": url,
            "updatedAt": int(time.time()),
            "nodeCount": node_count,
            "userinfo": userinfo,
        }
        self._save(data)

    def get_subscription(self) -> Optional[Dict[str, Any]]:
        subscription = self._load().get("subscription")
        return dict(subscription) if isinstance(subscription, dict) else None

    def set_active(self, profile_id: str) -> bool:
        data = self._load()
        if not any(item.get("id") == profile_id for item in data["items"]):
            return False
        data["activeId"] = profile_id
        self._save(data)
        return True

    def remove(self, profile_id: str) -> bool:
        data = self._load()
        before = len(data["items"])
        data["items"] = [i for i in data["items"] if i.get("id") != profile_id]
        if len(data["items"]) == before:
            return False
        if data.get("activeId") == profile_id:
            data["activeId"] = data["items"][0]["id"] if data["items"] else None
        self._save(data)
        return True

    def clear(self) -> None:
        self._save({"version": SCHEMA_VERSION, "activeId": None, "items": []})

    def set_latency(self, profile_id: str, latency_ms: Optional[int]) -> None:
        """Record a latency measurement (None = unreachable)."""
        data = self._load()
        for item in data["items"]:
            if item.get("id") == profile_id:
                item["latencyMs"] = latency_ms
                item["latencyTestedAt"] = int(time.time())
                break
        self._save(data)
