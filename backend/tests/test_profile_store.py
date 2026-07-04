"""Tests for backend.src.profile_store (schema v2 + legacy migration)."""

from backend.src.profile_store import LEGACY_KEY, PROFILES_KEY, ProfileStore


class _FakeSettings:
    def __init__(self, initial=None):
        self.data = dict(initial or {})
        self.commits = 0

    def getSetting(self, key, default=None):
        return self.data.get(key, default)

    def setSetting(self, key, value):
        self.data[key] = value

    def commit(self):
        self.commits += 1


def _profile(address="a.example.com", **extra):
    profile = {
        "protocol": "vless",
        "address": address,
        "port": 443,
        "network": "tcp",
        "security": "tls",
        "sourceUrl": f"vless://x@{address}:443",
        "configType": "single",
        "isValid": True,
    }
    profile.update(extra)
    return profile


def test_migrates_legacy_single_config():
    settings = _FakeSettings({LEGACY_KEY: _profile("legacy.example.com")})
    store = ProfileStore(settings)
    profiles = store.list_profiles()
    assert len(profiles) == 1
    assert profiles[0]["address"] == "legacy.example.com"
    assert store.get_active_id() == profiles[0]["id"]
    # Mirror preserved and id never leaks into the legacy key.
    assert settings.data[LEGACY_KEY]["address"] == "legacy.example.com"
    assert "id" not in settings.data[LEGACY_KEY]


def test_empty_start():
    store = ProfileStore(_FakeSettings())
    assert store.list_profiles() == []
    assert store.get_active() is None
    assert store.get_active_id() is None


def test_add_makes_active_and_mirrors():
    settings = _FakeSettings()
    store = ProfileStore(settings)
    first = store.add(_profile("one.example.com"))
    second = store.add(_profile("two.example.com"))
    assert store.get_active_id() == second
    assert settings.data[LEGACY_KEY]["address"] == "two.example.com"

    assert store.set_active(first)
    assert settings.data[LEGACY_KEY]["address"] == "one.example.com"
    assert not store.set_active("nonexistent")


def test_remove_reassigns_active_and_clears_mirror():
    settings = _FakeSettings()
    store = ProfileStore(settings)
    first = store.add(_profile("one.example.com"))
    second = store.add(_profile("two.example.com"))
    assert store.remove(second)  # active removed -> first becomes active
    assert store.get_active_id() == first
    assert settings.data[LEGACY_KEY]["address"] == "one.example.com"

    assert store.remove(first)
    assert store.list_profiles() == []
    assert settings.data[LEGACY_KEY] is None
    assert not store.remove(first)


def test_replace_all_for_subscription():
    settings = _FakeSettings()
    store = ProfileStore(settings)
    store.add(_profile("old.example.com"))
    ids = store.replace_all(
        [_profile("n1.example.com"), _profile("n2.example.com")]
    )
    assert len(ids) == 2
    profiles = store.list_profiles()
    assert [p["address"] for p in profiles] == ["n1.example.com", "n2.example.com"]
    assert store.get_active_id() == ids[0]
    assert settings.data[LEGACY_KEY]["address"] == "n1.example.com"


def test_replace_subscription_profiles_preserves_manual():
    settings = _FakeSettings()
    store = ProfileStore(settings)
    store.add(_profile("manual.example.com", configType="single"))
    store.add(_profile("old-sub.example.com", configType="subscription"))

    new_ids = store.replace_subscription_profiles(
        [
            _profile("s1.example.com", configType="subscription"),
            _profile("s2.example.com", configType="subscription"),
        ]
    )
    addresses = {p["address"] for p in store.list_profiles()}
    # Manual server survives; the old subscription server is gone; the two
    # new subscription servers are present (exact set — no substring checks).
    assert addresses == {"manual.example.com", "s1.example.com", "s2.example.com"}
    assert len(new_ids) == 2


def test_replace_subscription_keeps_active_manual():
    settings = _FakeSettings()
    store = ProfileStore(settings)
    manual = store.add(_profile("manual.example.com", configType="single"))
    store.add(_profile("sub.example.com", configType="subscription"))
    # Make the manual server active, then refresh the subscription.
    store.set_active(manual)
    store.replace_subscription_profiles(
        [_profile("s1.example.com", configType="subscription")]
    )
    # Active stays on the surviving manual server.
    assert store.get_active_id() == manual
    assert settings.data[LEGACY_KEY]["address"] == "manual.example.com"


def test_replace_subscription_keeps_active_server_by_endpoint():
    settings = _FakeSettings()
    store = ProfileStore(settings)
    store.add(_profile("keep.example.com", configType="subscription"))
    active = store.get_active_id()
    assert active is not None
    # Refresh: the same server (protocol/address/port) is still present.
    store.replace_subscription_profiles(
        [
            _profile("other.example.com", configType="subscription"),
            _profile("keep.example.com", configType="subscription"),
        ]
    )
    assert store.get_active()["address"] == "keep.example.com"


def test_subscription_name_derived_and_editable():
    settings = _FakeSettings()
    store = ProfileStore(settings)
    store.set_subscription("https://sub.example.com/link", 3)
    sub = store.get_subscription()
    assert sub["name"] == "sub.example.com"  # derived from the URL host

    # A custom name survives a refresh (same URL, no name passed).
    assert store.rename_subscription("Work VPN")
    store.set_subscription("https://sub.example.com/link", 5)
    assert store.get_subscription()["name"] == "Work VPN"

    # A different URL resets to a derived name.
    store.set_subscription("https://other.example.net/x", 2)
    assert store.get_subscription()["name"] == "other.example.net"


def test_rename_subscription_without_subscription():
    store = ProfileStore(_FakeSettings())
    assert store.rename_subscription("nope") is False


def test_refresh_interval_set_and_preserved_across_refresh():
    settings = _FakeSettings()
    store = ProfileStore(settings)
    # No subscription yet → nothing to schedule.
    assert store.set_refresh_interval(12) is False

    store.set_subscription("https://sub.example.com/link", 3)
    assert store.get_subscription()["refreshIntervalHours"] == 0  # default off
    assert store.set_refresh_interval(12) is True
    assert store.get_subscription()["refreshIntervalHours"] == 12

    # A refresh of the same URL keeps the interval (must not disable itself).
    store.set_subscription("https://sub.example.com/link", 5)
    assert store.get_subscription()["refreshIntervalHours"] == 12

    # A different subscription URL resets the interval to off.
    store.set_subscription("https://other.example.net/x", 2)
    assert store.get_subscription()["refreshIntervalHours"] == 0

    # Negative values are clamped to 0 (disabled).
    store.set_refresh_interval(-3)
    assert store.get_subscription()["refreshIntervalHours"] == 0


def test_clear_subscription():
    settings = _FakeSettings()
    store = ProfileStore(settings)
    store.add(_profile())
    store.set_subscription("https://sub.example.com/s", 1)
    assert store.get_subscription() is not None
    store.clear_subscription()
    assert store.get_subscription() is None


def test_clear():
    settings = _FakeSettings()
    store = ProfileStore(settings)
    store.add(_profile())
    store.clear()
    assert store.list_profiles() == []
    assert settings.data[LEGACY_KEY] is None


def test_set_latency():
    settings = _FakeSettings()
    store = ProfileStore(settings)
    profile_id = store.add(_profile())
    store.set_latency(profile_id, 42)
    assert store.get(profile_id)["latencyMs"] == 42
    assert store.get(profile_id)["latencyTestedAt"] > 0
    store.set_latency(profile_id, None)
    assert store.get(profile_id)["latencyMs"] is None


def test_corrupt_profiles_key_rebuilt():
    settings = _FakeSettings({PROFILES_KEY: "garbage"})
    store = ProfileStore(settings)
    assert store.list_profiles() == []
