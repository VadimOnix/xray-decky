"""
Xray Manager - Manages xray-core process lifecycle

Handles starting, stopping, and monitoring xray-core subprocess.
Generates xray-core configuration files from VLESSConfig.
"""

import asyncio
import json
import os
import tempfile
from typing import Dict, Any, Optional


class XrayManager:
    """
    Manages xray-core process lifecycle.

    Responsibilities:
    - Generate xray-core JSON configuration
    - Start/stop xray-core subprocess
    - Monitor process health
    - Handle process crashes
    """

    def __init__(self, xray_binary_path: str = "backend/out/xray-core"):
        """
        Initialize XrayManager.

        Args:
            xray_binary_path: Path to xray-core binary
        """
        self.xray_binary_path = xray_binary_path
        self.process: Optional[asyncio.subprocess.Process] = None
        self.config_file: Optional[str] = None
        self.process_id: Optional[int] = None

    def generate_config(
        self,
        vless_config: Dict[str, Any],
        tun_mode: bool = False,
        outbound_interface: Optional[str] = None,
    ) -> str:
        """
        Generate xray-core JSON configuration from VLESSConfig.

        Args:
            vless_config: VLESSConfig dictionary
            tun_mode: Whether to enable TUN mode
            outbound_interface: For TUN mode, bind proxy to this interface (e.g. wlan0)

        Returns:
            Path to generated config file
        """
        # Create temporary config file
        config_dir = tempfile.gettempdir()
        config_file = os.path.join(config_dir, f"xray-config-{os.getpid()}.json")

        # Generate xray-core config
        xray_config = self._build_xray_config(
            vless_config, tun_mode, outbound_interface
        )

        # Write config file
        with open(config_file, "w") as f:
            json.dump(xray_config, f, indent=2)

        self.config_file = config_file
        return config_file

    def _build_xray_config(
        self,
        vless_config: Dict[str, Any],
        tun_mode: bool,
        outbound_interface: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build xray-core JSON configuration structure.

        Args:
            vless_config: VLESSConfig dictionary
            tun_mode: Whether to enable TUN mode

        Returns:
            xray-core configuration dictionary
        """
        # Extract VLESS config components
        uuid = vless_config.get("uuid")
        address = vless_config.get("address")
        port = vless_config.get("port")
        flow = vless_config.get("flow")
        encryption = vless_config.get("encryption", "none")
        network = vless_config.get("network", "tcp")
        security = vless_config.get("security", "none")
        reality_config = vless_config.get("realityConfig", {})

        # Build outbound configuration (tag "proxy" for routing)
        outbound = {
            "protocol": "vless",
            "tag": "proxy",
            "settings": {
                "vnext": [
                    {
                        "address": address,
                        "port": port,
                        "users": [
                            {
                                "id": uuid,
                                "encryption": encryption,
                                "flow": flow if flow else "",
                            }
                        ],
                    }
                ]
            },
            "streamSettings": {
                "network": network,
                "security": security,
            },
        }

        # Add Reality-specific settings (CLIENT configuration)
        # Note: Client uses publicKey, serverName, shortId, fingerprint
        # Server uses privateKey, dest, xver - these are NOT for client!
        if security == "reality" and reality_config:
            outbound["streamSettings"]["realitySettings"] = {
                "serverName": reality_config.get("serverName", address),
                "publicKey": reality_config.get("publicKey", ""),
                "shortId": reality_config.get("shortId", ""),
                "fingerprint": reality_config.get("fingerprint", "chrome"),
            }

        # Network-specific settings
        if network == "ws":
            outbound["streamSettings"]["wsSettings"] = {"path": "/", "headers": {}}

        # TUN mode: bind proxy outbound to physical interface to bypass routing (avoid loop)
        if tun_mode and outbound_interface:
            outbound["streamSettings"]["sockopt"] = {"interface": outbound_interface}

        # Build complete config
        config = {
            "log": {"loglevel": "warning"},
            "inbounds": [],
            "outbounds": [outbound],
        }

        # Always add SOCKS proxy inbound (needed for System Proxy mode)
        # This allows System Proxy to work both with and without TUN mode
        config["inbounds"].append(
            {
                "protocol": "socks",
                "listen": "127.0.0.1",
                "port": 10808,  # Standard SOCKS port, avoids Steam ports
                "settings": {"udp": True},
                "tag": "socks",
            }
        )

        # Add HTTP proxy inbound (some apps prefer HTTP proxy)
        config["inbounds"].append(
            {
                "protocol": "http",
                "listen": "127.0.0.1",
                "port": 10809,  # HTTP proxy port
                "tag": "http",
            }
        )

        # Add TUN mode configuration if enabled
        if tun_mode:
            # Direct outbound for bypassing (private/LAN IPs - geoip:private)
            direct_outbound = {
                "protocol": "freedom",
                "settings": {"domainStrategy": "UseIP"},
                "tag": "direct",
            }

            # Routing: TUN inbound -> proxy (VLESS); private IPs bypass via direct
            # SOCKS/HTTP inbounds also route to proxy
            config["routing"] = {
                "domainStrategy": "IPIfNonMatch",
                "rules": [
                    # Bypass private/LAN IPs (127.x, 10.x, 192.168.x, etc.)
                    {"type": "field", "ip": ["geoip:private"], "outboundTag": "direct"},
                    # All TUN traffic goes through VLESS proxy
                    {"type": "field", "inboundTag": ["tun"], "outboundTag": "proxy"},
                    # SOCKS/HTTP inbound traffic goes through proxy
                    {
                        "type": "field",
                        "inboundTag": ["socks", "http"],
                        "outboundTag": "proxy",
                    },
                ],
            }

            # Add TUN inbound (xray-core will create TUN interface)
            # Xray docs: name, MTU, userLevel. Xray does NOT auto-modify system routing.
            config["inbounds"].append(
                {
                    "protocol": "tun",
                    "settings": {"name": "xray0", "MTU": 1500},
                    "tag": "tun",
                }
            )

            config["outbounds"].append(direct_outbound)

        return config

    async def start(self, config_file: str) -> Dict[str, Any]:
        """
        Start xray-core process with given config file.

        Args:
            config_file: Path to xray-core config file

        Returns:
            Dictionary with success status and process ID
        """
        try:
            # Check if binary exists
            if not os.path.exists(self.xray_binary_path):
                return {
                    "success": False,
                    "error": f"xray-core binary not found at {self.xray_binary_path}",
                    "errorCode": "BINARY_NOT_FOUND",
                }

            # Check if binary is executable
            if not os.access(self.xray_binary_path, os.X_OK):
                return {
                    "success": False,
                    "error": f"xray-core binary is not executable: {self.xray_binary_path}",
                    "errorCode": "BINARY_NOT_EXECUTABLE",
                }

            # Start xray-core subprocess
            self.process = await asyncio.create_subprocess_exec(
                self.xray_binary_path,
                "-config",
                config_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            self.process_id = self.process.pid
            self.config_file = config_file

            # Wait a moment to check if process started successfully
            await asyncio.sleep(0.5)

            if self.process.returncode is not None:
                # Process exited immediately (error)
                stderr = await self.process.stderr.read()
                error_msg = (
                    stderr.decode("utf-8", errors="ignore")
                    if stderr
                    else "Unknown error"
                )
                return {
                    "success": False,
                    "error": f"xray-core process failed to start: {error_msg}",
                    "errorCode": "PROCESS_START_FAILED",
                }

            return {"success": True, "processId": self.process_id}

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start xray-core: {str(e)}",
                "errorCode": "PROCESS_START_ERROR",
            }

    async def stop(self) -> Dict[str, Any]:
        """
        Stop xray-core process.

        Returns:
            Dictionary with success status
        """
        try:
            if self.process is None:
                return {"success": True, "message": "No process running"}

            # Terminate process
            self.process.terminate()

            # Wait for process to terminate (with timeout)
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                # Force kill if process doesn't terminate
                self.process.kill()
                await self.process.wait()

            # Cleanup config file
            if self.config_file and os.path.exists(self.config_file):
                try:
                    os.remove(self.config_file)
                except Exception:
                    pass  # Ignore cleanup errors

            self.process = None
            self.process_id = None
            self.config_file = None

            return {"success": True}

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to stop xray-core: {str(e)}",
                "errorCode": "PROCESS_STOP_ERROR",
            }

    def is_running(self) -> bool:
        """
        Check if xray-core process is running.

        Returns:
            True if process is running, False otherwise
        """
        if self.process is None:
            return False

        # Check if process is still alive
        return self.process.returncode is None

    def get_process_id(self) -> Optional[int]:
        """
        Get xray-core process ID.

        Returns:
            Process ID or None if not running
        """
        return self.process_id

    async def monitor(self) -> Dict[str, Any]:
        """
        Monitor xray-core process health.

        Returns:
            Dictionary with process status
        """
        if not self.is_running():
            return {"running": False, "processId": None}

        return {"running": True, "processId": self.process_id}
