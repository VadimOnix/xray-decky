"""Tests for the KillSwitch firewall lifecycle.

These tests mock ``asyncio.create_subprocess_exec`` so no real firewall rules
are touched. They assert the properties the previous implementation broke:
deactivation actually issues the commands that remove our rules, reports failure
when the chain is still hooked, and the rules match by uid (not the long-removed
--pid-owner match) across both IPv4 and IPv6.
"""

import asyncio
import os
from typing import List, Tuple
from unittest.mock import patch

from backend.src.kill_switch import KillSwitch, CHAIN, TUN_INTERFACE, _IPV6


class _FakeProcess:
    """Minimal stand-in for an asyncio subprocess."""

    def __init__(self, returncode: int):
        self.returncode = returncode

    async def communicate(self):
        return (b"", b"")


class _Recorder:
    """Records every iptables/ip6tables invocation and returns scripted codes.

    Each recorded entry is (binary, args_without_lock_flag).
    """

    def __init__(self, ipv6_present: bool = True, hooked: bool = False):
        self.calls: List[Tuple[str, Tuple[str, ...]]] = []
        self.ipv6_present = ipv6_present
        # Whether "-C OUTPUT -j CHAIN" reports the jump as present.
        self.hooked = hooked
        self._delete_budget = {"iptables": 1, "ip6tables": 1}

    def __call__(self, *args, **kwargs) -> "_FakeProcess":
        binary = args[0]
        rest = list(args[1:])
        # Strip the "-w <n>" lock flag that _run prepends.
        if rest[:1] == ["-w"]:
            rest = rest[2:]
        self.calls.append((binary, tuple(rest)))

        if binary == _IPV6 and not self.ipv6_present:
            return _FakeProcess(127)

        if rest[:2] == ["-D", "OUTPUT"]:
            if self._delete_budget.get(binary, 0) > 0:
                self._delete_budget[binary] -= 1
                return _FakeProcess(0)
            return _FakeProcess(1)

        if rest[:2] == ["-C", "OUTPUT"]:
            return _FakeProcess(0 if self.hooked else 1)

        return _FakeProcess(0)

    def args_for(self, binary: str) -> List[Tuple[str, ...]]:
        return [a for b, a in self.calls if b == binary]


def _patch(recorder: "_Recorder"):
    async def _fake_exec(*args, **kwargs):
        return recorder(*args, **kwargs)

    return patch("asyncio.create_subprocess_exec", side_effect=_fake_exec)


def test_activate_creates_chain_and_hooks_output():
    ks = KillSwitch()
    rec = _Recorder()

    with _patch(rec):
        result = asyncio.run(ks.activate(4242))

    assert result["success"] is True
    assert ks.is_active is True
    v4 = rec.args_for("iptables")

    assert ("-N", CHAIN) in v4
    assert ("-A", CHAIN, "-j", "DROP") in v4
    assert ("-A", CHAIN, "-o", "lo", "-j", "ACCEPT") in v4
    assert ("-A", CHAIN, "-o", TUN_INTERFACE, "-j", "ACCEPT") in v4
    assert ("-I", "OUTPUT", "1", "-j", CHAIN) in v4
    # Owner match is uid-based (the supported match), never pid-based.
    uid = str(os.geteuid())
    assert ("-A", CHAIN, "-m", "owner", "--uid-owner", uid, "-j", "ACCEPT") in v4


def test_never_uses_removed_pid_owner_match():
    """Regression guard: --pid-owner was removed from modern kernels."""
    ks = KillSwitch()
    rec = _Recorder()
    with _patch(rec):
        asyncio.run(ks.activate(4242))
    assert all("--pid-owner" not in a for _, a in rec.calls)


def test_rules_applied_to_both_families():
    ks = KillSwitch()
    rec = _Recorder(ipv6_present=True)
    with _patch(rec):
        asyncio.run(ks.activate(4242))
    # The DROP rule is installed on both IPv4 and IPv6.
    assert ("-A", CHAIN, "-j", "DROP") in rec.args_for("iptables")
    assert ("-A", CHAIN, "-j", "DROP") in rec.args_for("ip6tables")


def test_activate_succeeds_when_ipv6_absent():
    ks = KillSwitch()
    rec = _Recorder(ipv6_present=False)
    with _patch(rec):
        result = asyncio.run(ks.activate(4242))
    assert result["success"] is True
    # IPv4 rules still applied.
    assert ("-A", CHAIN, "-j", "DROP") in rec.args_for("iptables")


def test_deactivate_removes_chain_and_jump():
    """The core regression: deactivate must actually delete the rules."""
    ks = KillSwitch()
    with _patch(_Recorder()):
        asyncio.run(ks.activate(4242))

    rec = _Recorder(hooked=False)
    with _patch(rec):
        result = asyncio.run(ks.deactivate())

    assert result["success"] is True
    assert ks.is_active is False
    v4 = rec.args_for("iptables")
    assert ("-D", "OUTPUT", "-j", CHAIN) in v4
    assert ("-F", CHAIN) in v4
    assert ("-X", CHAIN) in v4


def test_deactivate_reports_failure_when_still_hooked():
    """If teardown can't remove the jump, deactivate must not claim success."""
    ks = KillSwitch()
    with _patch(_Recorder()):
        asyncio.run(ks.activate(4242))

    rec = _Recorder(hooked=True)  # -C OUTPUT still finds the jump
    with _patch(rec):
        result = asyncio.run(ks.deactivate())

    assert result["success"] is False
    assert result["errorCode"] == "IPTABLES_FAILED"


def test_deactivate_when_not_active_is_safe():
    """Deactivating an inactive switch still tears down any stale chain."""
    ks = KillSwitch()
    rec = _Recorder(hooked=False)
    with _patch(rec):
        result = asyncio.run(ks.deactivate())
    assert result["success"] is True
    assert ("-X", CHAIN) in rec.args_for("iptables")


def test_activate_rolls_back_on_rule_failure():
    """If a chain rule fails to apply, no DROP is left hooked into OUTPUT."""
    ks = KillSwitch()

    class _FailDrop(_Recorder):
        def __call__(self, *args, **kwargs):
            proc = super().__call__(*args, **kwargs)
            rest = list(args[1:])
            if rest[:1] == ["-w"]:
                rest = rest[2:]
            if args[0] == "iptables" and rest == ["-A", CHAIN, "-j", "DROP"]:
                return _FakeProcess(1)
            return proc

    rec = _FailDrop()
    with _patch(rec):
        result = asyncio.run(ks.activate(4242))

    assert result["success"] is False
    assert result["errorCode"] == "IPTABLES_FAILED"
    assert ks.is_active is False
    assert ("-X", CHAIN) in rec.args_for("iptables")


def test_double_activate_updates_pid():
    ks = KillSwitch()
    with _patch(_Recorder()):
        asyncio.run(ks.activate(4242))
        result = asyncio.run(ks.activate(9999))
    assert result["success"] is True
    assert ks.xray_process_id == 9999
