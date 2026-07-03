"""Tests for the KillSwitch iptables lifecycle.

These tests mock ``asyncio.create_subprocess_exec`` so no real iptables rules
are touched. They assert the property that the previous implementation broke:
deactivation actually issues the iptables commands that remove our rules.
"""

import asyncio
from typing import List, Tuple
from unittest.mock import patch

from backend.src.kill_switch import KillSwitch, CHAIN


class _FakeProcess:
    """Minimal stand-in for an asyncio subprocess."""

    def __init__(self, returncode: int):
        self.returncode = returncode

    async def communicate(self):
        return (b"", b"")


class _IptablesRecorder:
    """Records every iptables invocation and returns scripted return codes.

    ``delete_hits`` controls how many times a ``-D OUTPUT -j CHAIN`` call
    succeeds before returning non-zero, so the teardown delete-loop terminates.
    """

    def __init__(self, delete_hits: int = 1):
        self.calls: List[List[str]] = []
        self._delete_budget = delete_hits

    def __call__(self, *args, **kwargs) -> "_FakeProcess":
        # args[0] is "iptables"; the rest are the actual iptables arguments.
        argv = list(args[1:])
        self.calls.append(argv)

        # The delete-jump loop keeps going while rc == 0; give it a finite
        # number of successes then fail so the loop exits.
        if argv[:2] == ["-D", "OUTPUT"]:
            if self._delete_budget > 0:
                self._delete_budget -= 1
                return _FakeProcess(0)
            return _FakeProcess(1)

        # A check that finds no existing jump returns non-zero (so activate
        # proceeds to insert one).
        if argv[:2] == ["-C", "OUTPUT"]:
            return _FakeProcess(1)

        return _FakeProcess(0)

    def commands(self) -> List[Tuple[str, ...]]:
        return [tuple(c) for c in self.calls]


def _patch(recorder: "_IptablesRecorder"):
    async def _fake_exec(*args, **kwargs):
        return recorder(*args, **kwargs)

    return patch("asyncio.create_subprocess_exec", side_effect=_fake_exec)


def test_activate_creates_chain_and_hooks_output():
    ks = KillSwitch()
    rec = _IptablesRecorder()

    with _patch(rec):
        result = asyncio.run(ks.activate(4242))

    assert result["success"] is True
    assert ks.is_active is True
    cmds = rec.commands()

    # Chain is created, the drop-all rule is added, and OUTPUT jumps to it.
    assert ("-N", CHAIN) in cmds
    assert ("-A", CHAIN, "-j", "DROP") in cmds
    assert ("-I", "OUTPUT", "1", "-j", CHAIN) in cmds
    # The allowed xray pid appears in an ACCEPT rule.
    assert any("4242" in c and "ACCEPT" in c for c in cmds)


def test_deactivate_removes_chain_and_jump():
    """The core regression: deactivate must actually delete the rules."""
    ks = KillSwitch()

    with _patch(_IptablesRecorder()):
        asyncio.run(ks.activate(4242))

    rec = _IptablesRecorder()
    with _patch(rec):
        result = asyncio.run(ks.deactivate())

    assert result["success"] is True
    assert ks.is_active is False
    cmds = rec.commands()

    # The OUTPUT jump is deleted, and the chain is flushed and removed.
    assert ("-D", "OUTPUT", "-j", CHAIN) in cmds
    assert ("-F", CHAIN) in cmds
    assert ("-X", CHAIN) in cmds


def test_deactivate_when_not_active_is_safe():
    """Deactivating an inactive switch still tears down any stale chain."""
    ks = KillSwitch()
    rec = _IptablesRecorder()

    with _patch(rec):
        result = asyncio.run(ks.deactivate())

    assert result["success"] is True
    cmds = rec.commands()
    # Even with no in-memory state, teardown targets the named chain.
    assert ("-X", CHAIN) in cmds


def test_activate_rolls_back_on_rule_failure():
    """If a chain rule fails to apply, no DROP is left hooked into OUTPUT."""
    ks = KillSwitch()

    class _FailDropRecorder(_IptablesRecorder):
        def __call__(self, *args, **kwargs):
            argv = list(args[1:])
            proc = super().__call__(*args, **kwargs)
            # Fail specifically when applying the DROP rule.
            if argv == ["-A", CHAIN, "-j", "DROP"]:
                return _FakeProcess(1)
            return proc

    rec = _FailDropRecorder()
    with _patch(rec):
        result = asyncio.run(ks.activate(4242))

    assert result["success"] is False
    assert result["errorCode"] == "IPTABLES_FAILED"
    assert ks.is_active is False
    cmds = rec.commands()
    # Rollback removed the chain; OUTPUT was never left with a dangling jump.
    assert ("-X", CHAIN) in cmds


def test_double_activate_is_idempotent():
    ks = KillSwitch()

    with _patch(_IptablesRecorder()):
        asyncio.run(ks.activate(4242))
        result = asyncio.run(ks.activate(9999))

    assert result["success"] is True
    # The second activate just updates the tracked pid.
    assert ks.xray_process_id == 9999
