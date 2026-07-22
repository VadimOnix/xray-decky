"""Tests for TUNManager.ensure_system_route (post-resume route repair)."""

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
