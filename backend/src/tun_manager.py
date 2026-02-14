"""
TUN Manager - Manages TUN mode privileges and interface

Handles privilege checking and TUN interface management for system-wide routing.
"""

import os
import asyncio
from typing import Dict, Any, Optional


class TUNManager:
    """
    Manages TUN mode privileges and interface.

    Responsibilities:
    - Check if plugin has required privileges (CAP_NET_ADMIN)
    - Test TUN interface creation
    - Manage TUN interface lifecycle
    """

    TUN_INTERFACE = "xray0"
    ROUTE_METRIC = 100

    def __init__(self):
        """Initialize TUNManager."""
        self.tun_interface: Optional[str] = None
        self.has_privileges: bool = False
        self.last_check: Optional[float] = None
        self._route_added: bool = False

    async def check_privileges(self) -> Dict[str, Any]:
        """
        Check if plugin has required privileges for TUN mode.

        Returns:
            Dictionary with privilege status
        """
        try:
            # Method 1: Try to create a test TUN interface
            # This requires CAP_NET_ADMIN or root privileges
            test_result = await self._test_tun_creation()

            if test_result["success"]:
                self.has_privileges = True
                return {"hasPrivileges": True, "method": "tun_creation_test"}

            # Method 2: Check if we can use ip command (requires CAP_NET_ADMIN)
            ip_result = await self._test_ip_command()

            if ip_result["success"]:
                self.has_privileges = True
                return {"hasPrivileges": True, "method": "ip_command_test"}

            # Method 3: Check if running with elevated privileges
            # Check if we can access /dev/net/tun
            tun_device_result = await self._test_tun_device_access()

            if tun_device_result["success"]:
                self.has_privileges = True
                return {"hasPrivileges": True, "method": "tun_device_access"}

            # No privileges detected
            self.has_privileges = False
            return {
                "hasPrivileges": False,
                "error": "Insufficient privileges. TUN mode requires CAP_NET_ADMIN or root privileges.",
                "errorCode": "PRIVILEGES_INSUFFICIENT",
            }

        except Exception as e:
            return {
                "hasPrivileges": False,
                "error": f"Failed to check privileges: {str(e)}",
                "errorCode": "PRIVILEGE_CHECK_ERROR",
            }

    async def _test_tun_creation(self) -> Dict[str, Any]:
        """
        Test TUN interface creation (requires privileges).

        Returns:
            Dictionary with test result
        """
        try:
            # Try to create a temporary TUN interface
            test_interface = "test-tun0"

            # Use ip command to create test interface
            process = await asyncio.create_subprocess_exec(
                "ip",
                "tuntap",
                "add",
                "mode",
                "tun",
                test_interface,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            await process.wait()

            if process.returncode == 0:
                # Success - clean up test interface
                cleanup_process = await asyncio.create_subprocess_exec(
                    "ip",
                    "tuntap",
                    "del",
                    "mode",
                    "tun",
                    test_interface,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await cleanup_process.wait()
                return {"success": True}
            else:
                stderr = await process.stderr.read()
                error_msg = (
                    stderr.decode("utf-8", errors="ignore")
                    if stderr
                    else "Permission denied"
                )
                return {"success": False, "error": error_msg}

        except FileNotFoundError:
            # ip command not found
            return {"success": False, "error": "ip command not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _test_ip_command(self) -> Dict[str, Any]:
        """
        Test if ip command works (basic privilege check).

        Returns:
            Dictionary with test result
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "ip",
                "link",
                "show",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            await process.wait()

            if process.returncode == 0:
                return {"success": True}
            else:
                return {"success": False, "error": "ip command failed"}

        except FileNotFoundError:
            return {"success": False, "error": "ip command not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _test_tun_device_access(self) -> Dict[str, Any]:
        """
        Test if we can access /dev/net/tun device.

        Returns:
            Dictionary with test result
        """
        try:
            tun_device = "/dev/net/tun"
            if os.path.exists(tun_device):
                # Try to open the device (read-only check)
                try:
                    with open(tun_device, "rb"):
                        pass
                    return {"success": True}
                except PermissionError:
                    return {"success": False, "error": "Permission denied"}
            else:
                return {"success": False, "error": "TUN device not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_physical_interface(self) -> Optional[str]:
        """Get the default route's interface (e.g. wlan0) for sockopt.interface binding."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "ip",
                "-4",
                "route",
                "show",
                "default",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            if proc.returncode != 0:
                return None
            out = await proc.stdout.read()
            for line in out.decode("utf-8", errors="ignore").strip().split("\n"):
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == "dev" and i + 1 < len(parts):
                        dev = parts[i + 1]
                        if dev and dev != self.TUN_INTERFACE:
                            return dev
                        break
        except Exception:
            pass
        return None

    async def setup_system_route(self) -> Dict[str, Any]:
        """
        Add default route via xray0. Xray's proxy outbound must use sockopt.interface
        to bind to the physical interface (wlan0) - that bypasses routing and avoids loop.
        """
        try:
            dev = self.TUN_INTERFACE
            for _ in range(20):
                proc = await asyncio.create_subprocess_exec(
                    "ip",
                    "link",
                    "show",
                    dev,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await proc.wait()
                if proc.returncode == 0:
                    break
                await asyncio.sleep(0.25)
            else:
                return {"success": False, "error": f"Interface {dev} did not appear"}

            proc = await asyncio.create_subprocess_exec(
                "ip",
                "route",
                "add",
                "default",
                "dev",
                dev,
                "metric",
                str(self.ROUTE_METRIC),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            if proc.returncode == 0:
                self._route_added = True
                return {"success": True}
            err = (await proc.stderr.read()).decode("utf-8", errors="ignore").strip()
            return {"success": False, "error": err}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def remove_system_route(self) -> Dict[str, Any]:
        """Remove default route via xray0. Also cleanup legacy fwmark rule if present."""
        try:
            # Remove legacy fwmark rule/table from previous versions (ignore errors)
            for args in [
                ["ip", "rule", "del", "fwmark", "0x206", "table", "100"],
                ["ip", "route", "del", "default", "table", "100"],
            ]:
                proc = await asyncio.create_subprocess_exec(
                    *args,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await proc.wait()
            if not self._route_added:
                return {"success": True}
            proc = await asyncio.create_subprocess_exec(
                "ip",
                "route",
                "del",
                "default",
                "dev",
                self.TUN_INTERFACE,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
            self._route_added = False
            return {"success": True}
        except Exception as e:
            self._route_added = False
            return {"success": False, "error": str(e)}

    async def create_tun_interface(
        self, interface_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Track TUN interface (xray-core creates it via config).

        Args:
            interface_name: Name for TUN interface (default: xray0)

        Returns:
            Dictionary with creation result
        """
        try:
            name = interface_name or self.TUN_INTERFACE
            self.tun_interface = name
            return {"success": True, "interface": name}
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create TUN interface: {str(e)}",
            }

    async def cleanup_tun_interface(self) -> Dict[str, Any]:
        """
        Cleanup TUN interface (xray-core handles this, but we track state).

        Returns:
            Dictionary with cleanup result
        """
        try:
            # xray-core will cleanup TUN interface when stopped
            # We just clear our tracking
            self.tun_interface = None
            return {"success": True}
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to cleanup TUN interface: {str(e)}",
            }

    def get_status(self) -> Dict[str, Any]:
        """
        Get current TUN manager status.

        Returns:
            Dictionary with status information
        """
        return {
            "hasPrivileges": self.has_privileges,
            "tunInterface": self.tun_interface,
        }
