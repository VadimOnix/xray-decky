"""
Xray Decky Plugin - Backend Entry Point

This module provides the Plugin class that serves as the backend entry point
for the Decky Loader plugin. All backend methods are defined here.
"""

import os
import asyncio
import time
from typing import Dict, Any, Optional
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

# Initialize SettingsManager
settings_dir = os.environ.get("DECKY_PLUGIN_SETTINGS_DIR", "")
if not settings_dir:
    raise RuntimeError("DECKY_PLUGIN_SETTINGS_DIR environment variable not set")

settings = SettingsManager(name="settings", settings_directory=settings_dir)
settings.read()

# Initialize XrayManager, TUNManager, and KillSwitch
xray_manager = XrayManager()
tun_manager = TUNManager()
kill_switch = KillSwitch()


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

    async def _unload(self):
        """
        Cleanup code called when the plugin is unloaded.
        """
        print("Xray Decky Plugin: Backend unloading")
        # Stop xray-core process if running
        connection_state = get_connection_state()
        if connection_state.status == ConnectionStatus.CONNECTED:
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
                    
                    # Create TUN interface tracking
                    await tun_manager.create_tun_interface("tun0")
                
                # Generate xray-core config
                config_file = xray_manager.generate_config(config, tun_mode)
                
                # Start xray-core
                result = await xray_manager.start(config_file)
                
                if not result.get("success", False):
                    error_msg = result.get("error", "Failed to start xray-core")
                    error_code = result.get("errorCode", ErrorCode.PROCESS_FAILED)
                    connection_state.set_error(error_msg, error_code)
                    return create_error_response(error_code, error_msg)
                
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
                
                # Stop xray-core
                result = await xray_manager.stop()
                
                if not result.get("success", False):
                    # Log error but still mark as disconnected
                    print(f"Warning: Failed to stop xray-core cleanly: {result.get('error')}")
                
                # Cleanup TUN interface if active
                tun_pref = settings.getSetting("tunMode", {})
                if tun_pref.get("enabled", False):
                    await tun_manager.cleanup_tun_interface()
                
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
