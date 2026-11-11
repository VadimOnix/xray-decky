"""Boot and resume behavior at the Decky backend boundary."""

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest


@pytest.fixture
def plugin(monkeypatch, tmp_path):
    settings = Mock()
    values = {"autoConnect": True, "vlessConfig": {"isValid": True}, "tunMode": {"enabled": True}}
    settings.getSetting.side_effect = values.get
    monkeypatch.setitem(sys.modules, "settings", SimpleNamespace(SettingsManager=Mock(return_value=settings)))
    monkeypatch.setenv("DECKY_PLUGIN_SETTINGS_DIR", str(tmp_path))
    source = Path(__file__).resolve().parents[1] / "main.py"
    spec = importlib.util.spec_from_file_location("decky_plugin_under_test", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    state = SimpleNamespace(status=module.ConnectionStatus.DISCONNECTED)
    monkeypatch.setattr(module, "get_connection_state", lambda: state)
    instance = module.Plugin()
    instance._supervisor = None
    instance._auto_connect_armed = True
    instance._outbound_interface = "wlan0"
    instance._toggle_connection = AsyncMock(return_value={"success": True})
    return module, instance, state


@pytest.mark.asyncio
async def test_waits_for_network_and_respects_manual_disconnect(plugin, monkeypatch):
    module, instance, _ = plugin
    interface = AsyncMock(side_effect=[None, "wlan0"])
    monkeypatch.setattr(module.tun_manager, "get_physical_interface", interface)
    await instance._check_connection()
    instance._toggle_connection.assert_not_awaited()
    await instance._check_connection()
    instance._toggle_connection.assert_awaited_once_with(True)
    instance._auto_connect_armed = False
    await instance._check_connection()
    assert instance._toggle_connection.await_count == 1


@pytest.mark.asyncio
async def test_resume_repairs_route_and_rebinds_on_interface_change(plugin, monkeypatch):
    module, instance, state = plugin
    state.status = module.ConnectionStatus.CONNECTED
    monkeypatch.setattr(module.active_core_manager, "is_running", lambda: True)
    monkeypatch.setattr(module.tun_manager, "get_physical_interface", AsyncMock(side_effect=["wlan0", "eth0"]))
    repair = AsyncMock(return_value={"success": True, "restored": True})
    monkeypatch.setattr(module.tun_manager, "ensure_system_route", repair)
    assert (await instance._check_connection())["routeRestored"]
    repair.assert_awaited_once()
    assert (await instance._check_connection())["routeRestored"]
    assert [call.args for call in instance._toggle_connection.await_args_list] == [(False,), (True,)]
