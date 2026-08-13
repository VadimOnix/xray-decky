"""Tests for TUNManager route helpers (post-resume repair, tunnel bypass)."""

import asyncio
from unittest.mock import patch

from backend.src.tun_manager import TUNManager


class _FakeStream:
    def __init__(self, data: bytes):
        self._data = data

    async def read(self):
        return self._data


class _FakeProcess:
    def __init__(self, returncode: int, stdout: bytes = b"", stderr: bytes = b""):
        self.returncode = returncode
        self.stdout = _FakeStream(stdout)
        self.stderr = _FakeStream(stderr)

    async def wait(self):
        return self.returncode


class _Recorder:
    """Scripted asyncio.create_subprocess_exec replacement."""

    def __init__(self, script):
        # script: list of (args_predicate, process) applied in order of match.
        self.script = script
        self.calls = []

    async def __call__(self, *args, **kwargs):
        self.calls.append(list(args))
        for predicate, process in self.script:
            if predicate(list(args)):
                return process
        raise AssertionError(f"Unexpected command: {args}")


def test_route_present_is_noop():
    recorder = _Recorder(
        [
            (
                lambda a: a[:3] == ["ip", "route", "show"],
                _FakeProcess(0, stdout=b"default dev xray0 scope link metric 1\n"),
            )
        ]
    )
    with patch("asyncio.create_subprocess_exec", recorder):
        result = asyncio.run(TUNManager().ensure_system_route())
    assert result == {"success": True, "restored": False}
    # Only the check ran; no route was added.
    assert all(a[:3] != ["ip", "route", "add"] for a in recorder.calls)


def test_missing_route_is_restored():
    recorder = _Recorder(
        [
            (
                lambda a: a[:3] == ["ip", "route", "show"],
                _FakeProcess(0, stdout=b""),
            ),
            (
                lambda a: a[:3] == ["ip", "link", "show"],
                _FakeProcess(0),
            ),
            (
                lambda a: a[:3] == ["ip", "route", "add"],
                _FakeProcess(0),
            ),
        ]
    )
    with patch("asyncio.create_subprocess_exec", recorder):
        result = asyncio.run(TUNManager().ensure_system_route())
    assert result["success"] is True
    assert result["restored"] is True
    assert any(a[:3] == ["ip", "route", "add"] for a in recorder.calls)


def test_restore_failure_reported():
    recorder = _Recorder(
        [
            (
                lambda a: a[:3] == ["ip", "route", "show"],
                _FakeProcess(0, stdout=b""),
            ),
            (
                lambda a: a[:3] == ["ip", "link", "show"],
                _FakeProcess(1),  # interface never appears
            ),
        ]
    )
    async def instant_sleep(_delay):
        return None

    with patch("asyncio.create_subprocess_exec", recorder):
        with patch("asyncio.sleep", instant_sleep):
            result = asyncio.run(TUNManager().ensure_system_route())
    assert result["success"] is False
    assert result["restored"] is False
    assert result["error"]


# --- get_tunnel_bypass_interface ---

# Both defaults present: setup_system_route's metric-100 route outranks the
# physical default, so every socket the plugin opens enters the tunnel.
_TUN_HIJACKED = (
    b"default dev xray0 scope link metric 100 \n"
    b"default via 192.168.30.1 dev wlan0 proto dhcp src 192.168.30.209 metric 600 \n"
)
_NO_TUN = b"default via 192.168.30.1 dev wlan0 proto dhcp metric 600 \n"


def _route_recorder(stdout: bytes, returncode: int = 0):
    return _Recorder(
        [
            (
                lambda a: a[:4] == ["ip", "-4", "route", "show"],
                _FakeProcess(returncode, stdout=stdout),
            )
        ]
    )


def test_bypass_interface_is_physical_nic_while_tun_hijacks_default():
    recorder = _route_recorder(_TUN_HIJACKED)
    with patch("asyncio.create_subprocess_exec", recorder):
        assert asyncio.run(TUNManager().get_tunnel_bypass_interface()) == "wlan0"


def test_no_bypass_interface_when_tun_route_absent():
    # Nothing to bypass: the physical default is already the winning route.
    recorder = _route_recorder(_NO_TUN)
    with patch("asyncio.create_subprocess_exec", recorder):
        assert asyncio.run(TUNManager().get_tunnel_bypass_interface()) is None


def test_no_bypass_interface_when_only_tun_route_exists():
    recorder = _route_recorder(b"default dev xray0 scope link metric 100 \n")
    with patch("asyncio.create_subprocess_exec", recorder):
        assert asyncio.run(TUNManager().get_tunnel_bypass_interface()) is None


def test_bypass_interface_none_when_ip_command_fails():
    recorder = _route_recorder(b"", returncode=1)
    with patch("asyncio.create_subprocess_exec", recorder):
        assert asyncio.run(TUNManager().get_tunnel_bypass_interface()) is None


def test_physical_interface_still_skips_tun_device():
    recorder = _route_recorder(_TUN_HIJACKED)
    with patch("asyncio.create_subprocess_exec", recorder):
        assert asyncio.run(TUNManager().get_physical_interface()) == "wlan0"
