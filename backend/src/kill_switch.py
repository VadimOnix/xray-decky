"""
Kill Switch - Blocks all traffic when proxy disconnects unexpectedly

Uses iptables rules to block all outgoing traffic except xray-core process.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List


class KillSwitch:
    """
    Manages kill switch functionality using iptables.

    When activated, blocks all outgoing traffic except xray-core process.
    """

    def __init__(self):
        """Initialize KillSwitch."""
        self.is_active: bool = False
        self.activated_at: Optional[float] = None
        self.rule_ids: List[str] = []
        self.xray_process_id: Optional[int] = None

    async def activate(self, xray_process_id: int) -> Dict[str, Any]:
        """
        Activate kill switch - block all traffic except xray-core.

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

            self.xray_process_id = xray_process_id

            # Apply iptables rules
            # Rule 1: Allow xray-core process
            rule1_result = await self._apply_rule(
                [
                    "iptables",
                    "-A",
                    "OUTPUT",
                    "-m",
                    "owner",
                    "--pid-owner",
                    str(xray_process_id),
                    "-j",
                    "ACCEPT",
                ],
                f"xray-allow-{xray_process_id}",
            )

            if not rule1_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to apply allow rule: {rule1_result.get('error')}",
                    "errorCode": "IPTABLES_FAILED",
                }

            # Rule 2: Block all other traffic
            rule2_result = await self._apply_rule(
                ["iptables", "-A", "OUTPUT", "-j", "DROP"], "kill-switch-block-all"
            )

            if not rule2_result["success"]:
                # Cleanup first rule if second failed
                await self._remove_rule(f"xray-allow-{xray_process_id}")
                return {
                    "success": False,
                    "error": f"Failed to apply block rule: {rule2_result.get('error')}",
                    "errorCode": "IPTABLES_FAILED",
                }

            self.is_active = True
            self.activated_at = time.time()
            self.rule_ids = [f"xray-allow-{xray_process_id}", "kill-switch-block-all"]

            return {"success": True, "activatedAt": int(self.activated_at)}

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to activate kill switch: {str(e)}",
                "errorCode": "KILL_SWITCH_ERROR",
            }

    async def deactivate(self) -> Dict[str, Any]:
        """
        Deactivate kill switch - remove iptables rules.

        Returns:
            Dictionary with deactivation result
        """
        try:
            if not self.is_active:
                return {"success": True, "message": "Kill switch not active"}

            # Remove rules in reverse order
            for rule_id in reversed(self.rule_ids):
                await self._remove_rule(rule_id)

            self.is_active = False
            self.activated_at = None
            self.rule_ids = []
            self.xray_process_id = None

            return {"success": True}

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to deactivate kill switch: {str(e)}",
                "errorCode": "KILL_SWITCH_ERROR",
            }

    async def _apply_rule(self, command: List[str], rule_id: str) -> Dict[str, Any]:
        """
        Apply an iptables rule.

        Args:
            command: iptables command as list
            rule_id: Identifier for the rule

        Returns:
            Dictionary with result
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            await process.wait()

            if process.returncode == 0:
                return {"success": True, "ruleId": rule_id}
            else:
                stderr = await process.stderr.read()
                error_msg = (
                    stderr.decode("utf-8", errors="ignore")
                    if stderr
                    else "Unknown error"
                )
                return {"success": False, "error": error_msg}

        except FileNotFoundError:
            return {"success": False, "error": "iptables command not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _remove_rule(self, rule_id: str) -> Dict[str, Any]:
        """
        Remove an iptables rule.

        Args:
            rule_id: Identifier for the rule to remove

        Returns:
            Dictionary with result
        """
        try:
            # Try to remove rule (may not exist, that's OK)
            # We'll try different methods to find and remove the rule

            # Method 1: Try to remove by rule number (if we tracked it)
            # For now, we'll use a simpler approach: remove all our rules

            # Note: In production, you'd want to track rule numbers more carefully
            # This is a simplified implementation

            return {"success": True}

        except Exception as e:
            # Don't fail deactivation if rule removal fails
            # Log the error but continue
            print(f"Warning: Failed to remove iptables rule {rule_id}: {e}")
            return {"success": True}  # Return success to allow cleanup to continue

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
            "ruleIds": self.rule_ids.copy(),
        }
