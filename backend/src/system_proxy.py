"""
System Proxy Manager - Manages system-wide proxy settings on Linux

Configures system proxy using gsettings (GNOME/GTK) and kwriteconfig5 (KDE/Qt).
Based on nekoray's QvProxyConfigurator implementation.
"""

import asyncio
import os
import shutil
from typing import Dict, Any, Optional, List, Tuple


class SystemProxyManager:
    """
    Manages system-wide proxy settings.
    
    Responsibilities:
    - Set system proxy for HTTP/HTTPS/SOCKS
    - Clear system proxy settings
    - Detect desktop environment (GNOME, KDE, etc.)
    """
    
    # Default ports
    DEFAULT_SOCKS_PORT = 10808
    DEFAULT_HTTP_PORT = 10809
    PROXY_ADDRESS = "127.0.0.1"
    
    def __init__(self):
        """Initialize SystemProxyManager."""
        self._is_active: bool = False
        self._socks_port: Optional[int] = None
        self._http_port: Optional[int] = None
    
    def _is_kde(self) -> bool:
        """Check if running in KDE desktop environment."""
        xdg_desktop = os.environ.get("XDG_SESSION_DESKTOP", "").lower()
        return xdg_desktop in ("kde", "plasma")
    
    def _get_config_path(self) -> str:
        """Get XDG config path."""
        return os.environ.get(
            "XDG_CONFIG_HOME",
            os.path.expanduser("~/.config")
        )
    
    async def _run_command(self, program: str, args: List[str]) -> Tuple[int, str, str]:
        """
        Run a command asynchronously.
        
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                program,
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            return (
                proc.returncode or 0,
                stdout.decode('utf-8', errors='ignore'),
                stderr.decode('utf-8', errors='ignore')
            )
        except FileNotFoundError:
            return (-1, "", f"Command not found: {program}")
        except Exception as e:
            return (-1, "", str(e))
    
    async def _has_gsettings(self) -> bool:
        """Check if gsettings is available."""
        return shutil.which("gsettings") is not None
    
    async def _has_kwriteconfig5(self) -> bool:
        """Check if kwriteconfig5 is available."""
        return shutil.which("kwriteconfig5") is not None
    
    async def set_system_proxy(
        self,
        socks_port: int = DEFAULT_SOCKS_PORT,
        http_port: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Set system proxy settings.
        
        Args:
            socks_port: SOCKS5 proxy port (default: 10808)
            http_port: HTTP proxy port (optional, uses socks_port if not set)
        
        Returns:
            Dictionary with success status
        """
        address = self.PROXY_ADDRESS
        has_http = http_port is not None and 0 < http_port < 65536
        has_socks = 0 < socks_port < 65536
        
        if not has_socks and not has_http:
            return {"success": False, "error": "Invalid port configuration"}
        
        # Use socks_port for HTTP if http_port not specified
        effective_http_port = http_port if has_http else socks_port
        
        actions: List[Tuple[str, List[str]]] = []
        results: List[bool] = []
        
        # Check available tools
        has_gs = await self._has_gsettings()
        has_kw = await self._has_kwriteconfig5()
        is_kde = self._is_kde()
        config_path = self._get_config_path()
        
        if not has_gs and not has_kw:
            return {
                "success": False,
                "error": "Neither gsettings nor kwriteconfig5 available"
            }
        
        # Configure GNOME/GTK proxy settings via gsettings
        if has_gs:
            # Set proxy mode to manual
            actions.append(("gsettings", ["set", "org.gnome.system.proxy", "mode", "manual"]))
            
            # Configure HTTP proxy for http, https, ftp
            for protocol in ["http", "https", "ftp"]:
                actions.append((
                    "gsettings",
                    ["set", f"org.gnome.system.proxy.{protocol}", "host", address]
                ))
                actions.append((
                    "gsettings",
                    ["set", f"org.gnome.system.proxy.{protocol}", "port", str(effective_http_port)]
                ))
            
            # Configure SOCKS proxy
            if has_socks:
                actions.append((
                    "gsettings",
                    ["set", "org.gnome.system.proxy.socks", "host", address]
                ))
                actions.append((
                    "gsettings",
                    ["set", "org.gnome.system.proxy.socks", "port", str(socks_port)]
                ))
        
        # Configure KDE/Qt proxy settings via kwriteconfig5
        if has_kw and is_kde:
            kioslaverc = os.path.join(config_path, "kioslaverc")
            
            # HTTP proxy for http, https, ftp
            for protocol in ["http", "https", "ftp"]:
                actions.append((
                    "kwriteconfig5",
                    [
                        "--file", kioslaverc,
                        "--group", "Proxy Settings",
                        "--key", f"{protocol}Proxy",
                        f"http://{address} {effective_http_port}"
                    ]
                ))
            
            # SOCKS proxy
            if has_socks:
                actions.append((
                    "kwriteconfig5",
                    [
                        "--file", kioslaverc,
                        "--group", "Proxy Settings",
                        "--key", "socksProxy",
                        f"socks://{address} {socks_port}"
                    ]
                ))
            
            # Set proxy type to manual (1)
            actions.append((
                "kwriteconfig5",
                [
                    "--file", kioslaverc,
                    "--group", "Proxy Settings",
                    "--key", "ProxyType",
                    "1"
                ]
            ))
            
            # Notify KIO to reload proxy config
            actions.append((
                "dbus-send",
                [
                    "--type=signal",
                    "/KIO/Scheduler",
                    "org.kde.KIO.Scheduler.reparseSlaveConfiguration",
                    "string:''"
                ]
            ))
        
        # Execute all actions
        for program, args in actions:
            returncode, _, stderr = await self._run_command(program, args)
            results.append(returncode == 0)
            if returncode != 0 and stderr:
                print(f"SystemProxy: {program} {' '.join(args)} failed: {stderr}")
        
        success_count = results.count(True)
        total_count = len(results)
        
        if success_count == 0:
            return {"success": False, "error": "All proxy configuration commands failed"}
        
        self._is_active = True
        self._socks_port = socks_port
        self._http_port = effective_http_port
        
        return {
            "success": True,
            "configured": f"{success_count}/{total_count}",
            "socksPort": socks_port,
            "httpPort": effective_http_port
        }
    
    async def clear_system_proxy(self) -> Dict[str, Any]:
        """
        Clear system proxy settings.
        
        Returns:
            Dictionary with success status
        """
        actions: List[Tuple[str, List[str]]] = []
        results: List[bool] = []
        
        has_gs = await self._has_gsettings()
        has_kw = await self._has_kwriteconfig5()
        is_kde = self._is_kde()
        config_path = self._get_config_path()
        
        # Clear GNOME/GTK proxy settings
        if has_gs:
            actions.append((
                "gsettings",
                ["set", "org.gnome.system.proxy", "mode", "none"]
            ))
        
        # Clear KDE/Qt proxy settings
        if has_kw and is_kde:
            kioslaverc = os.path.join(config_path, "kioslaverc")
            
            # Set proxy type to none (0)
            actions.append((
                "kwriteconfig5",
                [
                    "--file", kioslaverc,
                    "--group", "Proxy Settings",
                    "--key", "ProxyType",
                    "0"
                ]
            ))
            
            # Notify KIO to reload proxy config
            actions.append((
                "dbus-send",
                [
                    "--type=signal",
                    "/KIO/Scheduler",
                    "org.kde.KIO.Scheduler.reparseSlaveConfiguration",
                    "string:''"
                ]
            ))
        
        # Execute all actions
        for program, args in actions:
            returncode, _, stderr = await self._run_command(program, args)
            results.append(returncode == 0)
            if returncode != 0 and stderr:
                print(f"SystemProxy: {program} {' '.join(args)} failed: {stderr}")
        
        self._is_active = False
        self._socks_port = None
        self._http_port = None
        
        return {"success": True}
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current system proxy status.
        
        Returns:
            Dictionary with status information
        """
        return {
            "isActive": self._is_active,
            "socksPort": self._socks_port,
            "httpPort": self._http_port,
            "address": self.PROXY_ADDRESS if self._is_active else None
        }
