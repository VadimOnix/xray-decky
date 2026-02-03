"""
Xray Decky Plugin - Backend Entry Point

This module provides the Plugin class that serves as the backend entry point
for the Decky Loader plugin. All backend methods are defined here.
"""

import os
import sys
import ssl
import asyncio
import socket
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional


def _get_lan_ip() -> str:
    """
    Determine the host's LAN IP (not 127.0.0.1) so the import page URL is reachable
    from other devices on the same network. Tries: (1) outgoing socket to 8.8.8.8,
    (2) hostname -I, (3) ip route get 8.8.8.8. Falls back to 127.0.0.1 only if all fail.
    """
    # 1) Outgoing UDP socket: usually gives the interface IP used for default route
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            if ip and ip != "127.0.0.1":
                return ip
    except Exception:
        pass
    # 2) Linux: hostname -I returns space-separated IPs; first is typically primary
    try:
        out = subprocess.check_output(
            ["hostname", "-I"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2,
        )
        for part in out.strip().split():
            part = part.strip()
            if part and not part.startswith("127."):
                return part
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    # 3) ip route get 8.8.8.8 → parse "src" address
    try:
        out = subprocess.check_output(
            ["ip", "-4", "route", "get", "8.8.8.8"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2,
        )
        for line in out.splitlines():
            if "src" in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == "src" and i + 1 < len(parts):
                        ip = parts[i + 1].strip()
                        if ip and ip != "127.0.0.1":
                            return ip
                        break
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return "127.0.0.1"

# Add plugin directory to Python path for backend module imports
PLUGIN_DIR = Path(__file__).resolve().parent
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from settings import SettingsManager
from backend.src.config_parser import (
    validate_vless_url,
    parse_vless_url,
    parse_subscription_url,
    build_vless_config,
)
from backend.src.error_codes import (
    ErrorCode,
    create_error_response,
    create_success_response,
)
from backend.src.xray_manager import XrayManager
from backend.src.connection_manager import get_connection_state, ConnectionStatus
from backend.src.tun_manager import TUNManager
from backend.src.kill_switch import KillSwitch
from backend.src.system_proxy import SystemProxyManager
from backend.src.import_server import create_import_app
from backend.src.cert_utils import ensure_cert_key
from aiohttp import web

# Initialize SettingsManager
settings_dir = os.environ.get("DECKY_PLUGIN_SETTINGS_DIR", "")
if not settings_dir:
    raise RuntimeError("DECKY_PLUGIN_SETTINGS_DIR environment variable not set")

settings = SettingsManager(name="settings", settings_directory=settings_dir)
settings.read()

# Resolve xray-core path: deployed uses bin/, dev uses backend/out/
def _resolve_xray_path(plugin_dir: Path) -> str:
    for candidate in (plugin_dir / "bin" / "xray-core", plugin_dir / "backend" / "out" / "xray-core"):
        if candidate.exists():
            return str(candidate)
    return str(plugin_dir / "backend" / "out" / "xray-core")  # fallback for clearer error

# Initialize XrayManager, TUNManager, KillSwitch, and SystemProxyManager
xray_manager = XrayManager(xray_binary_path=_resolve_xray_path(PLUGIN_DIR))
tun_manager = TUNManager()
kill_switch = KillSwitch()
system_proxy_manager = SystemProxyManager()


class Plugin:
    """
    Main plugin class for Xray Decky Plugin.
    
    All backend methods that can be called from the frontend are defined here.
    Methods are async and return dictionaries with success/error information.
    """

    async def _main(self):
        """
        Long-running code that executes for the plugin's lifetime.
        Called when the plugin is loaded.
        """
        print("Xray Decky Plugin: Backend initialized")
        # Load connection state from settings
        from backend.src.connection_manager import load_connection_state_from_settings
        load_connection_state_from_settings(settings)

        # Start import HTTPS server (TLS self-signed cert so Paste works from any device).
        # ImportServerConfig: port from settings, default 8765, range 1024–65535.
        # Bind to 0.0.0.0 so the import page is reachable from LAN (QR scan). If preferred port is in use, try next ports.
        import_server_config = settings.getSetting("importServer", {"port": 8765})
        port = int(import_server_config.get("port", 8765))
        port = max(1024, min(65535, port))
        static_dir = Path(__file__).resolve().parent / "backend" / "static"
        runtime_dir = os.environ.get("DECKY_PLUGIN_RUNTIME_DIR", "")
        ssl_context = None
        if static_dir.is_dir() and runtime_dir:
            try:
                Path(runtime_dir).mkdir(parents=True, exist_ok=True)
                cert_path, key_path = ensure_cert_key(Path(runtime_dir))
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                ssl_context.load_cert_chain(str(cert_path), str(key_path))
                ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            except Exception as e:
                print(f"Xray Decky Plugin: Import server TLS cert failed: {e}. Import server not started.")
                self._import_runner = None
                ssl_context = None
        if static_dir.is_dir() and ssl_context is not None:
            async def _notify_vless_saved():
                """Notify frontend that VLESS config was saved (e.g. from import page)."""
                try:
                    from decky import emit
                    await emit("vless_config_updated")
                except Exception as e:
                    print(f"Xray Decky Plugin: Failed to emit vless_config_updated: {e}")

            self._import_runner = None
            runner = None
            for attempt in range(11):  # try port, port+1, ... port+10
                try_port = port + attempt
                if try_port > 65535:
                    break
                try:
                    import_app = create_import_app(settings, static_dir, on_vless_saved=_notify_vless_saved)
                    runner = web.AppRunner(import_app)
                    await runner.setup()
                    site = web.TCPSite(runner, "0.0.0.0", try_port, ssl_context=ssl_context)
                    await site.start()
                    self._import_runner = runner
                    if try_port != port:
                        import_server_config["port"] = try_port
                        settings.setSetting("importServer", import_server_config)
                        settings.commit()
                        print(f"Xray Decky Plugin: Port {port} in use, using {try_port}. Import server listening on 0.0.0.0:{try_port} (HTTPS)")
                    else:
                        print(f"Xray Decky Plugin: Import server listening on 0.0.0.0:{try_port} (HTTPS)")
                    break
                except OSError as e:
                    if runner is not None:
                        await runner.cleanup()
                        runner = None
                    if attempt == 0:
                        print(f"Xray Decky Plugin: Port {try_port} failed: {e}, trying next ports...")
                    if attempt == 10:
                        self._import_runner = None
                        print(f"Xray Decky Plugin: Import server could not start on ports {port}-{port+10}. Check firewall or free a port.")
        elif not runtime_dir:
            self._import_runner = None
            print("Xray Decky Plugin: DECKY_PLUGIN_RUNTIME_DIR not set, import server not started")
        elif not static_dir.is_dir():
            self._import_runner = None
            print("Xray Decky Plugin: backend/static not found, import server not started")

    async def _unload(self):
        """
        Cleanup code called when the plugin is unloaded.
        """
        print("Xray Decky Plugin: Backend unloading")
        # Stop import HTTP server
        if getattr(self, "_import_runner", None) is not None:
            await self._import_runner.cleanup()
            self._import_runner = None
        
        # Clear system proxy if active
        system_proxy_pref = settings.getSetting("systemProxy", {})
        if system_proxy_pref.get("enabled", False):
            await system_proxy_manager.clear_system_proxy()
            system_proxy_pref["enabled"] = False
            settings.setSetting("systemProxy", system_proxy_pref)
            settings.commit()
        
        # Stop xray-core process if running
        connection_state = get_connection_state()
        if connection_state.status == ConnectionStatus.CONNECTED:
            tun_pref = settings.getSetting("tunMode", {})
            if tun_pref.get("enabled", False):
                await tun_manager.remove_system_route()
                await tun_manager.cleanup_tun_interface()
            await xray_manager.stop()
            connection_state.set_disconnected()
        
        # Deactivate kill switch if active
        if kill_switch.get_status().get("isActive", False):
            await kill_switch.deactivate()

    # SettingsManager wrapper methods
    async def settings_read(self) -> Dict[str, Any]:
        """Read settings from SettingsManager."""
        try:
            settings.read()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def settings_commit(self) -> Dict[str, Any]:
        """Commit settings to SettingsManager."""
        try:
            settings.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def settings_getSetting(self, key: str, defaults: Any) -> Dict[str, Any]:
        """Get a setting value from SettingsManager."""
        try:
            value = settings.getSetting(key, defaults)
            return {"success": True, "value": value}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def settings_setSetting(self, key: str, value: Any) -> Dict[str, Any]:
        """Set a setting value in SettingsManager."""
        try:
            settings.setSetting(key, value)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # VLESS Configuration Management
    async def import_vless_config(self, url: str) -> Dict[str, Any]:
        """
        Import and validate a VLESS configuration URL.
        
        Args:
            url: VLESS URL string (vless://... or base64 subscription)
        
        Returns:
            {
                'success': bool,
                'config': VLESSConfig | None,
                'error': str | None
            }
        """
        try:
            # Validate URL format
            is_valid, error_msg = validate_vless_url(url)
            if not is_valid:
                return create_error_response(ErrorCode.INVALID_URL, error_msg)
            
            # Try parsing as single node first
            parsed = parse_vless_url(url)
            config_type = "single"
            
            # If not single node, try subscription
            if not parsed:
                parsed_configs = parse_subscription_url(url)
                if not parsed_configs:
                    return create_error_response(ErrorCode.INVALID_URL, "Failed to parse VLESS URL")
                
                # For subscription, use first node (can be extended later)
                if len(parsed_configs) > 0:
                    parsed = parsed_configs[0]
                    config_type = "subscription"
                else:
                    return create_error_response(ErrorCode.INVALID_URL, "Subscription contains no valid nodes")
            
            # Build complete config
            config = build_vless_config(parsed, url, config_type)
            config["lastValidatedAt"] = int(time.time())
            
            # Store in SettingsManager
            settings.setSetting("vlessConfig", config)
            settings.commit()
            
            return create_success_response({"config": config})
            
        except Exception as e:
            return create_error_response(ErrorCode.UNKNOWN_ERROR, f"Failed to import config: {str(e)}")

    async def get_vless_config(self) -> Dict[str, Any]:
        """
        Get stored VLESS configuration.
        
        Returns:
            {
                'config': VLESSConfig | None,
                'exists': bool
            }
        """
        try:
            config = settings.getSetting("vlessConfig", None)
            exists = config is not None
            return {"config": config, "exists": exists}
        except Exception as e:
            return create_error_response(ErrorCode.UNKNOWN_ERROR, f"Failed to get config: {str(e)}")

    async def get_import_server_url(self) -> Dict[str, Any]:
        """
        Get URL for the import page (for QR code). Resolves LAN IP (not 127.0.0.1)
        and port from importServer.port so devices on the same network can open the page.
        Returns https baseUrl so the page is in a secure context and Paste works.
        
        Returns:
            { 'baseUrl': 'https://{lan_ip}:{port}', 'path': '/import' }
        """
        try:
            import_server_config = settings.getSetting("importServer", {"port": 8765})
            port = int(import_server_config.get("port", 8765))
            port = max(1024, min(65535, port))
            local_ip = _get_lan_ip()
            base_url = f"https://{local_ip}:{port}"
            return {"baseUrl": base_url, "path": "/import"}
        except Exception as e:
            return create_error_response(ErrorCode.UNKNOWN_ERROR, f"Failed to get import URL: {str(e)}")

    async def validate_vless_config(self) -> Dict[str, Any]:
        """
        Re-validate stored VLESS configuration.
        
        Returns:
            {
                'isValid': bool,
                'error': str | None
            }
        """
        try:
            config = settings.getSetting("vlessConfig", None)
            if not config:
                return {
                    "isValid": False,
                    "error": "No VLESS configuration stored",
                }
            
            # Re-validate the source URL
            source_url = config.get("sourceUrl", "")
            if not source_url:
                config["isValid"] = False
                config["validationError"] = "Missing source URL"
                settings.setSetting("vlessConfig", config)
                settings.commit()
                return {
                    "isValid": False,
                    "error": "Missing source URL",
                }
            
            is_valid, error_msg = validate_vless_url(source_url)
            config["isValid"] = is_valid
            config["lastValidatedAt"] = int(time.time())
            
            if not is_valid:
                config["validationError"] = error_msg or "Validation failed"
                settings.setSetting("vlessConfig", config)
                settings.commit()
                return {
                    "isValid": False,
                    "error": error_msg or "Validation failed",
                }
            
            # Clear validation error if valid
            if "validationError" in config:
                del config["validationError"]
            
            settings.setSetting("vlessConfig", config)
            settings.commit()
            
            return {
                "isValid": True,
            }
            
        except Exception as e:
            return {
                "isValid": False,
                "error": f"Validation error: {str(e)}",
            }

    # TUN Mode Management
    async def check_tun_privileges(self) -> Dict[str, Any]:
        """
        Check if plugin has required privileges for TUN mode.
        
        Returns:
            {
                'hasPrivileges': bool,
                'error': str | None
            }
        """
        try:
            result = await tun_manager.check_privileges()
            
            # Update TUN mode preference with privilege status
            tun_pref = settings.getSetting("tunMode", {})
            tun_pref["hasPrivileges"] = result.get("hasPrivileges", False)
            tun_pref["privilegeCheckAt"] = int(time.time())
            if "error" in result:
                tun_pref["privilegeError"] = result["error"]
            else:
                tun_pref.pop("privilegeError", None)
            settings.setSetting("tunMode", tun_pref)
            settings.commit()
            
            return result
            
        except Exception as e:
            return {
                "hasPrivileges": False,
                "error": f"Failed to check privileges: {str(e)}",
                "errorCode": "PRIVILEGE_CHECK_ERROR"
            }

    async def get_tun_mode_status(self) -> Dict[str, Any]:
        """
        Get TUN mode preference and status.
        
        Returns:
            {
                'enabled': bool,
                'hasPrivileges': bool,
                'tunInterface': str | None,
                'isActive': bool
            }
        """
        try:
            tun_pref = settings.getSetting("tunMode", {})
            enabled = tun_pref.get("enabled", False)
            has_privileges = tun_pref.get("hasPrivileges", False)
            
            # Check current privileges if not checked recently
            if not has_privileges or tun_pref.get("privilegeCheckAt", 0) < time.time() - 3600:
                privilege_result = await tun_manager.check_privileges()
                has_privileges = privilege_result.get("hasPrivileges", False)
            
            tun_status = tun_manager.get_status()
            tun_interface = tun_status.get("tunInterface")
            
            # Check if TUN is active (interface exists and connection is active)
            connection_state = get_connection_state()
            is_active = (
                enabled and
                has_privileges and
                connection_state.status == ConnectionStatus.CONNECTED and
                tun_interface is not None
            )
            
            return {
                "enabled": enabled,
                "hasPrivileges": has_privileges,
                "tunInterface": tun_interface,
                "isActive": is_active
            }
            
        except Exception as e:
            return {
                "enabled": False,
                "hasPrivileges": False,
                "tunInterface": None,
                "isActive": False,
                "error": str(e)
            }

    async def toggle_tun_mode(self, enabled: bool) -> Dict[str, Any]:
        """
        Toggle TUN mode preference.
        
        Args:
            enabled: True to enable, False to disable
        
        Returns:
            {
                'success': bool,
                'enabled': bool,
                'hasPrivileges': bool,
                'error': str | None
            }
        """
        try:
            # Check privileges first
            privilege_result = await tun_manager.check_privileges()
            has_privileges = privilege_result.get("hasPrivileges", False)
            
            if enabled and not has_privileges:
                return create_error_response(
                    ErrorCode.PRIVILEGES_INSUFFICIENT,
                    "TUN mode requires elevated privileges. Please complete installation steps."
                )
            
            # Update preference
            tun_pref = settings.getSetting("tunMode", {})
            tun_pref["enabled"] = enabled
            tun_pref["hasPrivileges"] = has_privileges
            if enabled:
                tun_pref["lastEnabledAt"] = int(time.time())
            else:
                tun_pref["lastDisabledAt"] = int(time.time())
            settings.setSetting("tunMode", tun_pref)
            settings.commit()
            
            return create_success_response({
                "enabled": enabled,
                "hasPrivileges": has_privileges
            })
            
        except Exception as e:
            return create_error_response(
                ErrorCode.UNKNOWN_ERROR,
                f"Failed to toggle TUN mode: {str(e)}"
            )

    # Connection Management
    async def toggle_connection(self, enable: bool) -> Dict[str, Any]:
        """
        Toggle proxy connection on/off.
        
        Args:
            enable: True to connect, False to disconnect
        
        Returns:
            {
                'success': bool,
                'status': str,  # 'connected', 'disconnected', 'error'
                'error': str | None,
                'processId': int | None
            }
        """
        connection_state = get_connection_state()
        
        try:
            if enable:
                # Connect
                # Check if already connected
                if connection_state.status == ConnectionStatus.CONNECTED:
                    return create_success_response({
                        "status": "connected",
                        "processId": connection_state.xray_process_id
                    })
                
                # Load and validate config
                config = settings.getSetting("vlessConfig", None)
                if not config:
                    connection_state.set_error("No VLESS config stored", ErrorCode.NO_CONFIG)
                    return create_error_response(ErrorCode.NO_CONFIG)
                
                if not config.get("isValid", False):
                    connection_state.set_error("VLESS config is invalid", ErrorCode.INVALID_CONFIG)
                    return create_error_response(ErrorCode.INVALID_CONFIG)
                
                # Set connecting status
                connection_state.set_connecting()
                
                # Get TUN mode preference
                tun_pref = settings.getSetting("tunMode", {})
                tun_mode = tun_pref.get("enabled", False)
                
                # If TUN mode is enabled, check privileges
                if tun_mode:
                    has_privileges = tun_pref.get("hasPrivileges", False)
                    if not has_privileges:
                        # Re-check privileges
                        privilege_result = await tun_manager.check_privileges()
                        has_privileges = privilege_result.get("hasPrivileges", False)
                        
                        if not has_privileges:
                            connection_state.set_error(
                                "TUN mode requires elevated privileges",
                                ErrorCode.PRIVILEGES_INSUFFICIENT
                            )
                            return create_error_response(
                                ErrorCode.PRIVILEGES_INSUFFICIENT,
                                "TUN mode requires elevated privileges. Please complete installation steps."
                            )
                    
                    await tun_manager.create_tun_interface()
                
                # TUN: get physical interface for sockopt.interface (avoids routing loop)
                outbound_if = await tun_manager.get_physical_interface() if tun_mode else None
                if tun_mode and not outbound_if:
                    connection_state.set_error(
                        "TUN: could not determine physical interface",
                        ErrorCode.UNKNOWN_ERROR,
                    )
                    return create_error_response(
                        ErrorCode.UNKNOWN_ERROR,
                        "TUN mode: could not get default route interface. Check network.",
                    )
                
                config_file = xray_manager.generate_config(config, tun_mode, outbound_if)
                
                # Start xray-core
                result = await xray_manager.start(config_file)
                
                if not result.get("success", False):
                    error_msg = result.get("error", "Failed to start xray-core")
                    error_code = result.get("errorCode", ErrorCode.PROCESS_FAILED)
                    connection_state.set_error(error_msg, error_code)
                    return create_error_response(error_code, error_msg)
                
                # TUN: policy routing via fwmark - xray outbound uses table 100, rest uses xray0
                if tun_mode:
                    route_result = await tun_manager.setup_system_route()
                    if not route_result.get("success"):
                        await xray_manager.stop()
                        connection_state.set_error(
                            f"TUN route failed: {route_result.get('error', 'Unknown')}",
                            ErrorCode.UNKNOWN_ERROR,
                        )
                        return create_error_response(
                            ErrorCode.UNKNOWN_ERROR,
                            f"Could not set TUN route: {route_result.get('error', 'Unknown')}",
                        )
                    
                    # Auto-enable System Proxy when TUN mode is active
                    # Only set autoEnabled if user had not manually enabled proxy
                    proxy_result = await system_proxy_manager.set_system_proxy(
                        socks_port=10808,
                        http_port=10809
                    )
                    if proxy_result.get("success"):
                        system_proxy_pref = settings.getSetting("systemProxy", {})
                        was_manually_enabled = system_proxy_pref.get("enabled", False) and not system_proxy_pref.get(
                            "autoEnabled", False
                        )
                        system_proxy_pref["enabled"] = True
                        if not was_manually_enabled:
                            system_proxy_pref["autoEnabled"] = True  # Mark as auto-enabled by TUN
                        system_proxy_pref["lastEnabledAt"] = int(time.time())
                        settings.setSetting("systemProxy", system_proxy_pref)
                    # Note: Don't fail connection if system proxy fails - TUN still works
                
                # Update connection state
                process_id = result.get("processId")
                connection_state.set_connected(process_id, config_file, config)
                
                # Deactivate kill switch if active (connection restored)
                kill_switch_pref = settings.getSetting("killSwitch", {})
                if kill_switch_pref.get("isActive", False):
                    await kill_switch.deactivate()
                    kill_switch_pref["isActive"] = False
                    kill_switch_pref["deactivatedAt"] = int(time.time())
                    settings.setSetting("killSwitch", kill_switch_pref)
                    settings.commit()
                
                # Persist connection state
                settings.setSetting("connectionState", {
                    "status": "connected",
                    "connectedAt": int(time.time())
                })
                settings.commit()
                
                return create_success_response({
                    "status": "connected",
                    "processId": process_id
                })
            
            else:
                # Disconnect
                if connection_state.status == ConnectionStatus.DISCONNECTED:
                    return create_success_response({
                        "status": "disconnected"
                    })
                
                # Clear system proxy only if it was auto-enabled by TUN mode
                # Preserve user's manual system proxy preference when TUN disconnects
                system_proxy_pref = settings.getSetting("systemProxy", {})
                if system_proxy_pref.get("autoEnabled", False):
                    await system_proxy_manager.clear_system_proxy()
                    system_proxy_pref["enabled"] = False
                    system_proxy_pref["autoEnabled"] = False
                    settings.setSetting("systemProxy", system_proxy_pref)
                
                # TUN: remove route first, then stop xray
                tun_pref = settings.getSetting("tunMode", {})
                if tun_pref.get("enabled", False):
                    await tun_manager.remove_system_route()
                    await tun_manager.cleanup_tun_interface()
                
                # Stop xray-core
                result = await xray_manager.stop()
                
                if not result.get("success", False):
                    # Log error but still mark as disconnected
                    print(f"Warning: Failed to stop xray-core cleanly: {result.get('error')}")
                
                # Update connection state
                connection_state.set_disconnected()
                
                # Check if kill switch should be activated (unexpected disconnect)
                kill_switch_pref = settings.getSetting("killSwitch", {})
                if kill_switch_pref.get("enabled", False) and connection_state.xray_process_id:
                    # This was an unexpected disconnect, activate kill switch
                    kill_result = await kill_switch.activate(connection_state.xray_process_id)
                    if kill_result.get("success"):
                        kill_switch_pref["isActive"] = True
                        kill_switch_pref["activatedAt"] = int(time.time())
                        connection_state.set_blocked()
                    settings.setSetting("killSwitch", kill_switch_pref)
                    settings.commit()
                
                # Persist connection state
                settings.setSetting("connectionState", {
                    "status": "disconnected" if not kill_switch_pref.get("isActive", False) else "blocked",
                    "disconnectedAt": int(time.time())
                })
                settings.commit()
                
                return create_success_response({
                    "status": "disconnected" if not kill_switch_pref.get("isActive", False) else "blocked"
                })
                
        except Exception as e:
            connection_state.set_error(f"Connection error: {str(e)}", ErrorCode.UNKNOWN_ERROR)
            return create_error_response(ErrorCode.UNKNOWN_ERROR, f"Connection error: {str(e)}")

    async def get_connection_status(self) -> Dict[str, Any]:
        """
        Get current connection status.
        
        Returns:
            {
                'status': str,  # 'disconnected', 'connecting', 'connected', 'error', 'blocked'
                'connectedAt': int | None,  # Unix timestamp
                'errorMessage': str | None,
                'processId': int | None,
                'uptime': int | None  # Seconds
            }
        """
        connection_state = get_connection_state()
        
        # Check if process is still running
        if connection_state.status == ConnectionStatus.CONNECTED:
            if not xray_manager.is_running():
                # Process died unexpectedly
                process_id = connection_state.xray_process_id
                connection_state.set_error("xray-core process terminated unexpectedly", ErrorCode.PROCESS_FAILED)
                
                # Check if kill switch should be activated
                kill_switch_pref = settings.getSetting("killSwitch", {})
                if kill_switch_pref.get("enabled", False) and process_id:
                    # Activate kill switch
                    kill_result = await kill_switch.activate(process_id)
                    if kill_result.get("success"):
                        kill_switch_pref["isActive"] = True
                        kill_switch_pref["activatedAt"] = int(time.time())
                        connection_state.set_blocked()
                        settings.setSetting("killSwitch", kill_switch_pref)
                        settings.commit()
                
                # Cleanup TUN route if was active
                tun_pref = settings.getSetting("tunMode", {})
                if tun_pref.get("enabled", False):
                    await tun_manager.remove_system_route()
                
                # Cleanup
                await xray_manager.stop()
        
        # Return current status
        return connection_state.to_dict()
    
    # Kill Switch Management
    async def toggle_kill_switch(self, enabled: bool) -> Dict[str, Any]:
        """
        Toggle kill switch preference.
        
        Args:
            enabled: True to enable, False to disable
        
        Returns:
            {
                'success': bool,
                'enabled': bool
            }
        """
        try:
            kill_switch_pref = settings.getSetting("killSwitch", {})
            kill_switch_pref["enabled"] = enabled
            
            if enabled:
                kill_switch_pref["lastEnabledAt"] = int(time.time())
            else:
                kill_switch_pref["lastDisabledAt"] = int(time.time())
                # Deactivate if currently active
                if kill_switch_pref.get("isActive", False):
                    await kill_switch.deactivate()
                    kill_switch_pref["isActive"] = False
                    kill_switch_pref["deactivatedAt"] = int(time.time())
                    
                    # Update connection state if blocked
                    connection_state = get_connection_state()
                    if connection_state.status == ConnectionStatus.BLOCKED:
                        connection_state.set_disconnected()
            
            settings.setSetting("killSwitch", kill_switch_pref)
            settings.commit()
            
            return create_success_response({
                "enabled": enabled
            })
            
        except Exception as e:
            return create_error_response(
                ErrorCode.UNKNOWN_ERROR,
                f"Failed to toggle kill switch: {str(e)}"
            )

    async def get_kill_switch_status(self) -> Dict[str, Any]:
        """
        Get kill switch preference and active state.
        
        Returns:
            {
                'enabled': bool,
                'isActive': bool,  # Whether kill switch is currently blocking
                'activatedAt': int | None  # When kill switch was activated
            }
        """
        try:
            kill_switch_pref = settings.getSetting("killSwitch", {})
            enabled = kill_switch_pref.get("enabled", False)
            is_active = kill_switch_pref.get("isActive", False)
            activated_at = kill_switch_pref.get("activatedAt")
            
            # Sync with actual kill switch state
            kill_switch_status = kill_switch.get_status()
            is_active = kill_switch_status.get("isActive", False) or is_active
            
            return {
                "enabled": enabled,
                "isActive": is_active,
                "activatedAt": activated_at
            }
            
        except Exception as e:
            return {
                "enabled": False,
                "isActive": False,
                "error": str(e)
            }

    async def deactivate_kill_switch(self) -> Dict[str, Any]:
        """
        Manually deactivate kill switch (when user reconnects or disables).
        
        Returns:
            {
                'success': bool,
                'error': str | None
            }
        """
        try:
            result = await kill_switch.deactivate()
            
            if result.get("success"):
                kill_switch_pref = settings.getSetting("killSwitch", {})
                kill_switch_pref["isActive"] = False
                kill_switch_pref["deactivatedAt"] = int(time.time())
                settings.setSetting("killSwitch", kill_switch_pref)
                settings.commit()
                
                # Update connection state if blocked
                connection_state = get_connection_state()
                if connection_state.status == ConnectionStatus.BLOCKED:
                    connection_state.set_disconnected()
                
                return create_success_response()
            else:
                return create_error_response(
                    ErrorCode.IPTABLES_FAILED,
                    result.get("error", "Failed to deactivate kill switch")
                )
            
        except Exception as e:
            return create_error_response(
                ErrorCode.UNKNOWN_ERROR,
                f"Failed to deactivate kill switch: {str(e)}"
            )

    # System Proxy Management
    async def toggle_system_proxy(self, enabled: bool) -> Dict[str, Any]:
        """
        Toggle system proxy preference. When enabled, configures system to use
        local SOCKS/HTTP proxy (gsettings for GNOME, kwriteconfig5 for KDE).
        
        Args:
            enabled: True to enable, False to disable
        
        Returns:
            {
                'success': bool,
                'enabled': bool,
                'error': str | None
            }
        """
        try:
            system_proxy_pref = settings.getSetting("systemProxy", {})
            
            if enabled:
                # Check if connected - system proxy only works when xray is running
                connection_state = get_connection_state()
                if connection_state.status != ConnectionStatus.CONNECTED:
                    return create_error_response(
                        ErrorCode.NOT_CONNECTED,
                        "System proxy requires active connection. Please connect first."
                    )
                
                # Set system proxy (SOCKS 10808, HTTP 10809)
                result = await system_proxy_manager.set_system_proxy(
                    socks_port=10808,
                    http_port=10809
                )
                
                if not result.get("success"):
                    return create_error_response(
                        ErrorCode.UNKNOWN_ERROR,
                        result.get("error", "Failed to set system proxy")
                    )
                
                system_proxy_pref["enabled"] = True
                system_proxy_pref["autoEnabled"] = False  # Manual enable, not by TUN
                system_proxy_pref["lastEnabledAt"] = int(time.time())
                system_proxy_pref["socksPort"] = 10808
                system_proxy_pref["httpPort"] = 10809
            else:
                # Clear system proxy
                await system_proxy_manager.clear_system_proxy()
                system_proxy_pref["enabled"] = False
                system_proxy_pref["autoEnabled"] = False
                system_proxy_pref["lastDisabledAt"] = int(time.time())
            
            settings.setSetting("systemProxy", system_proxy_pref)
            settings.commit()
            
            return create_success_response({
                "enabled": enabled,
                "socksPort": 10808 if enabled else None,
                "httpPort": 10809 if enabled else None
            })
            
        except Exception as e:
            return create_error_response(
                ErrorCode.UNKNOWN_ERROR,
                f"Failed to toggle system proxy: {str(e)}"
            )

    async def get_system_proxy_status(self) -> Dict[str, Any]:
        """
        Get system proxy preference and status.
        
        Returns:
            {
                'enabled': bool,
                'isActive': bool,
                'socksPort': int | None,
                'httpPort': int | None
            }
        """
        try:
            system_proxy_pref = settings.getSetting("systemProxy", {})
            enabled = system_proxy_pref.get("enabled", False)
            
            # Get actual status from manager
            manager_status = system_proxy_manager.get_status()
            is_active = manager_status.get("isActive", False)
            
            return {
                "enabled": enabled,
                "isActive": is_active,
                "socksPort": manager_status.get("socksPort"),
                "httpPort": manager_status.get("httpPort"),
                "address": manager_status.get("address")
            }
            
        except Exception as e:
            return {
                "enabled": False,
                "isActive": False,
                "error": str(e)
            }
