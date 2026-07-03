"""
Kill Switch - Blocks all traffic when proxy disconnects unexpectedly

Uses a dedicated iptables chain (XRAY_KILLSWITCH) hooked into OUTPUT so that
the rules can always be removed cleanly, even after a plugin reload or crash
where the in-memory state is gone. When activated, blocks all outgoing traffic
except loopback and the xray-core process.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List, Tuple

# Dedicated chain name. Keeping our rules in their own chain means teardown is a
# surgical flush+delete that never touches the user's own firewall rules, and is
# idempotent: deactivate() works even if we no longer know which rules we added
# (e.g. after the plugin was reloaded while the kill switch was active).
CHAIN = "XRAY_KILLSWITCH"

# How many times to retry removing the OUTPUT->CHAIN jump. A previous session
# that crashed before cleanup could have left more than one jump in place.
_MAX_JUMP_DELETES = 10


class KillSwitch:
    """
    Manages kill switch functionality using a dedicated iptables chain.

    When activated, blocks all outgoing traffic except loopback and xray-core.
    """

    def __init__(self):
        """Initialize KillSwitch."""
        self.is_active: bool = False
        self.activated_at: Optional[float] = None
        self.xray_process_id: Optional[int] = None

    async def _run(self, args: List[str]) -> Tuple[int, str]:
        """
        Run an iptables command.

        Args:
            args: iptables arguments (without the leading "iptables")

        Returns:
            Tuple of (returncode, stderr text). returncode 127 means the
            iptables binary was not found.
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "iptables",
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await process.communicate()
            return process.returncode or 0, stderr.decode("utf-8", errors="ignore")
        except FileNotFoundError:
            return 127, "iptables command not found"
        except Exception as e:  # pragma: no cover - defensive
            return 1, str(e)

    async def activate(self, xray_process_id: int) -> Dict[str, Any]:
        """
        Activate kill switch - block all traffic except loopback and xray-core.

        Args:
            xray_process_id: Process ID of xray-core to allow

        Returns:
            Dictionary with activation result
        """
        try:
            if self.is_active:
                # Already active, just update process ID
                self.xray_process_id = xray_process_id
                return {"success": True, "message": "Kill switch already active"}

            # Always start from a clean slate: a prior session may have left the
            # chain or an OUTPUT jump behind. Ignore errors here (nothing to
            # remove is the normal case).
            await self._teardown()

            # Create the dedicated chain and make sure it is empty.
            await self._run(["-N", CHAIN])  # may already exist; flush handles it
            rc, err = await self._run(["-F", CHAIN])
            if rc != 0:
                await self._teardown()
                return {
                    "success": False,
                    "error": f"Failed to initialize kill switch chain: {err}",
                    "errorCode": "IPTABLES_FAILED",
                }

            # Rules inside the chain, in order:
            #   1. Always allow loopback (SOCKS/HTTP inbounds live on 127.0.0.1).
            #   2. Allow the xray-core process itself so the tunnel stays up.
            #   3. Drop everything else.
            # NOTE: the --pid-owner match is a known limitation (removed from
            # newer kernels' xt_owner); replacing it with a uid/cgroup or
            # interface-based match is tracked in the roadmap (Phase 0) and needs
            # on-device validation. This change only fixes rule *removal*.
            chain_rules = [
                ["-A", CHAIN, "-o", "lo", "-j", "ACCEPT"],
                [
                    "-A",
                    CHAIN,
                    "-m",
                    "owner",
                    "--pid-owner",
                    str(xray_process_id),
                    "-j",
                    "ACCEPT",
                ],
                ["-A", CHAIN, "-j", "DROP"],
            ]
            for rule in chain_rules:
                rc, err = await self._run(rule)
                if rc != 0:
                    await self._teardown()
                    return {
                        "success": False,
                        "error": f"Failed to apply kill switch rule: {err}",
                        "errorCode": "IPTABLES_FAILED",
                    }

            # Hook the chain into OUTPUT, avoiding a duplicate jump if one exists.
            rc, _ = await self._run(["-C", "OUTPUT", "-j", CHAIN])
            if rc != 0:
                rc, err = await self._run(["-I", "OUTPUT", "1", "-j", CHAIN])
                if rc != 0:
                    await self._teardown()
                    return {
                        "success": False,
                        "error": f"Failed to hook kill switch into OUTPUT: {err}",
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
        tracked rule numbers.

        Returns:
            Dictionary with deactivation result
        """
        try:
            await self._teardown()

            self.is_active = False
            self.activated_at = None
            self.xray_process_id = None

            return {"success": True}

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to deactivate kill switch: {str(e)}",
                "errorCode": "KILL_SWITCH_ERROR",
            }

    async def _teardown(self) -> None:
        """
        Remove every OUTPUT->CHAIN jump and delete the chain itself.

        Idempotent: missing chain / missing jump are treated as success. This is
        the operation that actually unblocks traffic, so it must never raise.
        """
        # Remove all jumps from OUTPUT (there may be duplicates from a prior run).
        for _ in range(_MAX_JUMP_DELETES):
            rc, _ = await self._run(["-D", "OUTPUT", "-j", CHAIN])
            if rc != 0:
                break

        # Flush and delete the chain. Ignore errors (chain may not exist).
        await self._run(["-F", CHAIN])
        await self._run(["-X", CHAIN])

    def get_status(self) -> Dict[str, Any]:
        """
        Get current kill switch status.

        Returns:
            Dictionary with status information
        """
        return {
            "isActive": self.is_active,
            "activatedAt": int(self.activated_at) if self.activated_at else None,
            "processId": self.xray_process_id,
            "chain": CHAIN,
        }
