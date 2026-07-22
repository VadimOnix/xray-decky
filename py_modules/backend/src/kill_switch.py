"""
Kill Switch - Blocks all traffic when the proxy is (or should be) up.

Uses a dedicated firewall chain (XRAY_KILLSWITCH) hooked into OUTPUT on both
IPv4 (iptables) and IPv6 (ip6tables) so the rules can always be removed cleanly,
even after a plugin reload or crash where the in-memory state is gone.

While active, the chain permits only:
  * loopback (SOCKS/HTTP inbounds and local DNS live on 127.0.0.1),
  * the TUN interface (game traffic entering the tunnel in TUN mode), and
  * traffic owned by the uid xray-core runs under (root under the "root" plugin
    flag) so the tunnel to the proxy server can be established/maintained.
Everything else is dropped, so if the tunnel goes down user/app traffic cannot
leak out the physical interface with the real address.

Matching notes:
  * We match by ``--uid-owner`` (the supported owner match) rather than
    ``--pid-owner``, which was removed from the kernel's xt_owner and is
    rejected by modern iptables ("owner match options" only lists uid/gid).
  * The rule set is applied to both IPv4 and IPv6; IPv6 is best-effort (skipped
    only when the ip6tables binary is entirely absent) so a leak cannot slip out
    over IPv6 when the system has a v6 stack.
  * NOTE: the exact permit set (interface/uid) has not been validated against a
    real Steam Deck in TUN mode; see docs/ROADMAP.md Phase 0.
"""

import asyncio
import os
import time
from typing import Dict, Any, Optional, List, Tuple

# Keep in sync with backend.src.tun_manager.TUNManager.TUN_INTERFACE.
TUN_INTERFACE = "xray0"

# Dedicated chain name. Keeping our rules in their own chain means teardown is a
# surgical flush+delete that never touches the user's own firewall rules, and is
# idempotent: deactivate() works even if we no longer know which rules we added
# (e.g. after the plugin was reloaded while the kill switch was active).
CHAIN = "XRAY_KILLSWITCH"

# iptables/ip6tables binaries (IPv4 is required; IPv6 is best-effort).
_IPV4 = "iptables"
_IPV6 = "ip6tables"

# Seconds to wait for the xtables lock so a concurrent firewall manager
# (NetworkManager, docker, ...) does not make our commands spuriously fail.
_LOCK_WAIT = "5"

# How many times to retry removing the OUTPUT->CHAIN jump. A previous session
# that crashed before cleanup could have left more than one jump in place.
_MAX_JUMP_DELETES = 10

# Return code from _run when the binary itself is missing.
_RC_NO_BINARY = 127


class KillSwitch:
    """
    Manages kill switch functionality using a dedicated firewall chain.

    When activated, blocks all outgoing traffic except loopback, the TUN
    interface, and traffic owned by the xray-core uid.
    """

    def __init__(self):
        """Initialize KillSwitch."""
        self.is_active: bool = False
        self.activated_at: Optional[float] = None
        self.xray_process_id: Optional[int] = None
        self.allow_uid: Optional[int] = None

    async def _run(self, cmd: str, args: List[str]) -> Tuple[int, str]:
        """
        Run an iptables/ip6tables command.

        Args:
            cmd: "iptables" or "ip6tables".
            args: arguments (without the leading binary name); "-w <n>" for the
                  xtables lock is prepended automatically.

        Returns:
            Tuple of (returncode, stderr text). returncode _RC_NO_BINARY means
            the binary was not found (e.g. no IPv6 stack).
        """
        try:
            process = await asyncio.create_subprocess_exec(
                cmd,
                "-w",
                _LOCK_WAIT,
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await process.communicate()
            return process.returncode or 0, stderr.decode("utf-8", errors="ignore")
        except FileNotFoundError:
            return _RC_NO_BINARY, f"{cmd} command not found"
        except Exception as e:  # pragma: no cover - defensive
            return 1, str(e)

    def _chain_rules(self) -> List[List[str]]:
        """The ACCEPT/DROP rules that go inside the chain, in order."""
        return [
            ["-A", CHAIN, "-o", "lo", "-j", "ACCEPT"],
            ["-A", CHAIN, "-o", TUN_INTERFACE, "-j", "ACCEPT"],
            ["-A", CHAIN, "-m", "owner", "--uid-owner", str(self.allow_uid), "-j", "ACCEPT"],
            ["-A", CHAIN, "-j", "DROP"],
        ]

    async def _apply_family(self, cmd: str, required: bool) -> Optional[str]:
        """
        Build and hook the chain for one address family.

        Returns None on success, or an error string on failure. When the binary
        is absent and the family is not required (IPv6), returns None (skip).
        """
        # Probe for the binary first so a missing ip6tables is a clean skip.
        rc, err = await self._run(cmd, ["-F", CHAIN])
        if rc == _RC_NO_BINARY:
            return None if not required else err
        # -F failing because the chain does not exist yet is fine; create it.
        await self._run(cmd, ["-N", CHAIN])
        rc, err = await self._run(cmd, ["-F", CHAIN])
        if rc != 0:
            return err

        for rule in self._chain_rules():
            rc, err = await self._run(cmd, rule)
            if rc != 0:
                return err

        # Hook the chain into OUTPUT, avoiding a duplicate jump if one exists.
        rc, _ = await self._run(cmd, ["-C", "OUTPUT", "-j", CHAIN])
        if rc != 0:
            rc, err = await self._run(cmd, ["-I", "OUTPUT", "1", "-j", CHAIN])
            if rc != 0:
                return err
        return None

    async def activate(self, xray_process_id: int) -> Dict[str, Any]:
        """
        Activate kill switch.

        Args:
            xray_process_id: PID of xray-core (kept for status/logging; the rules
                             match by uid, so they survive an xray restart).

        Returns:
            Dictionary with activation result.
        """
        try:
            if self.is_active:
                # Rules match by uid, not pid, so a new pid needs no rule change.
                self.xray_process_id = xray_process_id
                return {"success": True, "message": "Kill switch already active"}

            self.allow_uid = os.geteuid()

            # Always start from a clean slate: a prior session may have left the
            # chain or an OUTPUT jump behind.
            await self._teardown()

            # IPv4 is required; IPv6 is best-effort (skipped only if absent).
            err = await self._apply_family(_IPV4, required=True)
            if err is None:
                err = await self._apply_family(_IPV6, required=False)
            if err is not None:
                await self._teardown()
                return {
                    "success": False,
                    "error": f"Failed to apply kill switch rules: {err}",
                    "errorCode": "IPTABLES_FAILED",
                }

            self.is_active = True
            self.activated_at = time.time()
            self.xray_process_id = xray_process_id

            return {"success": True, "activatedAt": int(self.activated_at)}

        except Exception as e:
            # Best-effort cleanup so we never leave a half-applied DROP in place.
            await self._teardown()
            return {
                "success": False,
                "error": f"Failed to activate kill switch: {str(e)}",
                "errorCode": "KILL_SWITCH_ERROR",
            }

    async def deactivate(self) -> Dict[str, Any]:
        """
        Deactivate kill switch - remove the chain and its OUTPUT hook.

        Safe to call at any time, including after a plugin reload when the
        in-memory rule state was lost: teardown targets the named chain, not
        tracked rule numbers. Reports failure (instead of a false success) if the
        chain is still hooked into OUTPUT afterwards, so the UI cannot show
        "off" while traffic is still blocked.

        Returns:
            Dictionary with deactivation result.
        """
        try:
            await self._teardown()

            still_hooked = await self._chain_still_hooked()

            self.is_active = False
            self.activated_at = None
            self.xray_process_id = None
            self.allow_uid = None

            if still_hooked:
                return {
                    "success": False,
                    "error": (
                        "Kill switch rules could not be fully removed; the "
                        f"{CHAIN} chain is still active. Traffic may remain "
                        "blocked."
                    ),
                    "errorCode": "IPTABLES_FAILED",
                }
            return {"success": True}

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to deactivate kill switch: {str(e)}",
                "errorCode": "KILL_SWITCH_ERROR",
            }

    async def _teardown(self) -> None:
        """
        Remove every OUTPUT->CHAIN jump and delete the chain, on both families.

        Idempotent: missing chain / missing jump / missing binary are treated as
        success. This is the operation that actually unblocks traffic, so it must
        never raise.
        """
        for cmd in (_IPV4, _IPV6):
            # Remove all jumps from OUTPUT (duplicates possible from a prior run).
            for _ in range(_MAX_JUMP_DELETES):
                rc, _err = await self._run(cmd, ["-D", "OUTPUT", "-j", CHAIN])
                if rc != 0:
                    break
            # Flush and delete the chain. Ignore errors (chain may not exist).
            await self._run(cmd, ["-F", CHAIN])
            await self._run(cmd, ["-X", CHAIN])

    async def _chain_still_hooked(self) -> bool:
        """True if the OUTPUT->CHAIN jump still exists on any present family."""
        for cmd in (_IPV4, _IPV6):
            rc, _ = await self._run(cmd, ["-C", "OUTPUT", "-j", CHAIN])
            if rc == 0:
                return True
        return False

    def get_status(self) -> Dict[str, Any]:
        """
        Get current kill switch status.

        Returns:
            Dictionary with status information.
        """
        return {
            "isActive": self.is_active,
            "activatedAt": int(self.activated_at) if self.activated_at else None,
            "processId": self.xray_process_id,
            "chain": CHAIN,
        }
