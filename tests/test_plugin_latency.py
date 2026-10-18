"""Latency RPC selection and persistence without Decky lifecycle services."""

import asyncio
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from unittest.mock import AsyncMock

import pytest


class _FakeSettings:
    def __init__(self, **kwargs):
        self.data = {}

    def read(self):
        pass

    def getSetting(self, key, default=None):
        return deepcopy(self.data.get(key, default))

    def setSetting(self, key, value):
        self.data[key] = deepcopy(value)

    def commit(self):
        pass


@pytest.fixture
def plugin_module(monkeypatch, tmp_path):
    settings_module = ModuleType("settings")
    settings_module.SettingsManager = _FakeSettings
    monkeypatch.setitem(sys.modules, "settings", settings_module)
    monkeypatch.setenv("DECKY_PLUGIN_SETTINGS_DIR", str(tmp_path))

    spec = importlib.util.spec_from_file_location(
        "_xray_decky_latency_tests", Path(__file__).resolve().parents[1] / "main.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for address in ("active.example.com", "inactive.example.com"):
        module.profile_store.add(
            {
                "protocol": "vless",
                "address": address,
                "port": 443,
                "latencyMs": 99,
                "latencyTestedAt": 1,
            },
            make_active=False,
        )
    return module


@pytest.mark.parametrize("latency_ms", [42, None])
def test_single_profile_persists_only_target_latency(
    plugin_module, monkeypatch, latency_ms
):
    module = plugin_module
    store = module.profile_store
    active, target = store.list_profiles()
    active_id = store.get_active_id()
    active_config = deepcopy(module.settings.data["vlessConfig"])
    measure = AsyncMock(return_value={target["id"]: latency_ms})
    monkeypatch.setattr(module, "test_profiles", measure)
    plugin = module.Plugin()
    switch = AsyncMock()
    reconnect = AsyncMock()
    monkeypatch.setattr(plugin, "set_active_profile", switch)
    monkeypatch.setattr(plugin, "toggle_connection", reconnect)

    result = asyncio.run(plugin.test_profiles_latency(target["id"]))

    assert result == {"success": True, "results": {target["id"]: latency_ms}}
    measure.assert_awaited_once_with([target])
    assert store.get(active["id"]) == active
    updated = store.get(target["id"])
    assert updated["latencyMs"] == latency_ms
    assert updated["latencyTestedAt"] > target["latencyTestedAt"]
    assert store.get_active_id() == active_id
    assert module.settings.data["vlessConfig"] == active_config
    switch.assert_not_awaited()
    reconnect.assert_not_awaited()
    profiles = asyncio.run(plugin.get_profiles())
    assert profiles["profiles"] == store.list_profiles()
    assert profiles["activeId"] == active_id


@pytest.mark.parametrize("args", [(), (None,)])
def test_ping_all_accepts_omitted_or_none_id(plugin_module, monkeypatch, args):
    module = plugin_module
    profiles = module.profile_store.list_profiles()
    active_id = module.profile_store.get_active_id()
    results = {profiles[0]["id"]: 12, profiles[1]["id"]: None}
    measure = AsyncMock(return_value=results)
    monkeypatch.setattr(module, "test_profiles", measure)

    response = asyncio.run(module.Plugin().test_profiles_latency(*args))

    assert response == {"success": True, "results": results}
    measure.assert_awaited_once_with(profiles)
    for profile_id, latency_ms in results.items():
        profile = module.profile_store.get(profile_id)
        assert profile["latencyMs"] == latency_ms
        assert profile["latencyTestedAt"] > 1
    assert module.profile_store.get_active_id() == active_id


@pytest.mark.parametrize("profile_id", ["", "missing-profile"])
def test_invalid_id_never_falls_back_to_ping_all(
    plugin_module, monkeypatch, profile_id
):
    module = plugin_module
    before = deepcopy(module.settings.data)
    measure = AsyncMock()
    monkeypatch.setattr(module, "test_profiles", measure)

    response = asyncio.run(module.Plugin().test_profiles_latency(profile_id))

    assert response["success"] is False
    assert response["errorCode"] == "INVALID_CONFIG"
    measure.assert_not_awaited()
    assert module.settings.data == before


def test_measurement_failure_preserves_stored_results(plugin_module, monkeypatch):
    module = plugin_module
    target = module.profile_store.list_profiles()[1]
    before = deepcopy(module.settings.data)
    measure = AsyncMock(side_effect=RuntimeError("probe failed"))
    monkeypatch.setattr(module, "test_profiles", measure)

    response = asyncio.run(module.Plugin().test_profiles_latency(target["id"]))

    assert response["success"] is False
    assert response["errorCode"] == "UNKNOWN_ERROR"
    assert "probe failed" in response["error"]
    assert module.settings.data == before
