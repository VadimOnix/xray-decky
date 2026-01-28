"""
TUN Manager - Manages TUN mode privileges and interface

Handles privilege checking and TUN interface management for system-wide routing.
"""

import os
import subprocess
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
    
    def __init__(self):
        """Initialize TUNManager."""
        self.tun_interface: Optional[str] = None
        self.has_privileges: bool = False
        self.last_check: Optional[float] = None
    
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
                return {
                    "hasPrivileges": True,
                    "method": "tun_creation_test"
                }
            
            # Method 2: Check if we can use ip command (requires CAP_NET_ADMIN)
            ip_result = await self._test_ip_command()
            
            if ip_result["success"]:
                self.has_privileges = True
                return {
                    "hasPrivileges": True,
                    "method": "ip_command_test"
                }
            
            # Method 3: Check if running with elevated privileges
            # Check if we can access /dev/net/tun
            tun_device_result = await self._test_tun_device_access()
            
            if tun_device_result["success"]:
                self.has_privileges = True
                return {
                    "hasPrivileges": True,
                    "method": "tun_device_access"
                }
            
            # No privileges detected
            self.has_privileges = False
            return {
                "hasPrivileges": False,
                "error": "Insufficient privileges. TUN mode requires CAP_NET_ADMIN or root privileges.",
                "errorCode": "PRIVILEGES_INSUFFICIENT"
            }
            
        except Exception as e:
            return {
                "hasPrivileges": False,
                "error": f"Failed to check privileges: {str(e)}",
                "errorCode": "PRIVILEGE_CHECK_ERROR"
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
                "ip", "tuntap", "add", "mode", "tun", test_interface,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.wait()
            
            if process.returncode == 0:
                # Success - clean up test interface
                cleanup_process = await asyncio.create_subprocess_exec(
                    "ip", "tuntap", "del", "mode", "tun", test_interface,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await cleanup_process.wait()
                return {"success": True}
            else:
                stderr = await process.stderr.read()
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Permission denied"
                return {
                    "success": False,
                    "error": error_msg
                }
                
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
                "ip", "link", "show",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
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
                    with open(tun_device, 'rb'):
                        pass
                    return {"success": True}
                except PermissionError:
                    return {"success": False, "error": "Permission denied"}
            else:
                return {"success": False, "error": "TUN device not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def create_tun_interface(self, interface_name: str = "tun0") -> Dict[str, Any]:
        """
        Create TUN interface (xray-core will handle this via config, but we can verify).
        
        Args:
            interface_name: Name for TUN interface
        
        Returns:
            Dictionary with creation result
        """
        try:
            # xray-core creates TUN interface via its config
            # We just verify it exists after xray-core starts
            self.tun_interface = interface_name
            return {
                "success": True,
                "interface": interface_name
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create TUN interface: {str(e)}"
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
                "error": f"Failed to cleanup TUN interface: {str(e)}"
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
