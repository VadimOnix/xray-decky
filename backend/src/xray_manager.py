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

from .stats import API_PORT


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
            vless_config: Profile dictionary (see config_parser.parse_share_link);
                profiles imported before multi-protocol support lack the
                "protocol" key and default to VLESS.
            tun_mode: Whether to enable TUN mode

        Returns:
            xray-core configuration dictionary
        """
        protocol = vless_config.get("protocol", "vless")
        address = vless_config.get("address")
        port = vless_config.get("port")
        network = vless_config.get("network") or "tcp"
        security = vless_config.get("security") or "none"
        transport = vless_config.get("transport") or {}
        tls_config = vless_config.get("tlsConfig") or {}
        reality_config = vless_config.get("realityConfig") or {}

        # Protocol-specific outbound settings
        if protocol in ("vless", "vmess"):
            user: Dict[str, Any] = {"id": vless_config.get("uuid")}
            if protocol == "vless":
                user["encryption"] = vless_config.get("encryption") or "none"
                flow = vless_config.get("flow")
                user["flow"] = flow if flow else ""
            else:
                user["alterId"] = int(vless_config.get("alterId") or 0)
                user["security"] = vless_config.get("vmessSecurity") or "auto"
            settings = {
                "vnext": [{"address": address, "port": port, "users": [user]}]
            }
        elif protocol == "trojan":
            settings = {
                "servers": [
                    {
                        "address": address,
                        "port": port,
                        "password": vless_config.get("password"),
                    }
                ]
            }
        elif protocol == "shadowsocks":
            settings = {
                "servers": [
                    {
                        "address": address,
                        "port": port,
                        "method": vless_config.get("method"),
                        "password": vless_config.get("password"),
                    }
                ]
            }
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")

        stream: Dict[str, Any] = {"network": network, "security": security}

        # Transport-specific settings
        if network == "ws":
            ws_settings: Dict[str, Any] = {"path": transport.get("path") or "/"}
            if transport.get("host"):
                ws_settings["host"] = transport["host"]
            stream["wsSettings"] = ws_settings
        elif network == "grpc":
            grpc_settings: Dict[str, Any] = {
                "serviceName": transport.get("serviceName") or ""
            }
            if transport.get("authority"):
                grpc_settings["authority"] = transport["authority"]
            if transport.get("multiMode"):
                grpc_settings["multiMode"] = True
            stream["grpcSettings"] = grpc_settings
        elif network == "httpupgrade":
            hu_settings: Dict[str, Any] = {"path": transport.get("path") or "/"}
            if transport.get("host"):
                hu_settings["host"] = transport["host"]
            stream["httpupgradeSettings"] = hu_settings
        elif network == "xhttp":
            xhttp_settings: Dict[str, Any] = {"path": transport.get("path") or "/"}
            if transport.get("host"):
                xhttp_settings["host"] = transport["host"]
            if transport.get("mode"):
                xhttp_settings["mode"] = transport["mode"]
            stream["xhttpSettings"] = xhttp_settings
        elif network == "kcp":
            kcp_settings: Dict[str, Any] = {
                "header": {"type": transport.get("headerType") or "none"}
            }
            if transport.get("seed"):
                kcp_settings["seed"] = transport["seed"]
            stream["kcpSettings"] = kcp_settings
        elif network == "tcp" and transport.get("headerType") == "http":
            request: Dict[str, Any] = {}
            if transport.get("path"):
                request["path"] = [transport["path"]]
            if transport.get("host"):
                request["headers"] = {"Host": [transport["host"]]}
            stream["tcpSettings"] = {"header": {"type": "http", "request": request}}

        # Security-specific settings
        if security == "tls":
            tls_settings: Dict[str, Any] = {
                "serverName": tls_config.get("serverName")
                or transport.get("host")
                or address
            }
            if tls_config.get("alpn"):
                tls_settings["alpn"] = tls_config["alpn"]
            if tls_config.get("fingerprint"):
                tls_settings["fingerprint"] = tls_config["fingerprint"]
            if tls_config.get("allowInsecure"):
                tls_settings["allowInsecure"] = True
            stream["tlsSettings"] = tls_settings
        elif security == "reality" and reality_config:
            # CLIENT configuration only: publicKey, serverName, shortId,
            # fingerprint (never privateKey/dest/xver - those are server-side).
            reality_settings = {
                "serverName": reality_config.get("serverName", address),
                "publicKey": reality_config.get("publicKey", ""),
                "shortId": reality_config.get("shortId", ""),
                "fingerprint": reality_config.get("fingerprint", "chrome"),
            }
            if reality_config.get("spiderX"):
                reality_settings["spiderX"] = reality_config["spiderX"]
            stream["realitySettings"] = reality_settings

        # TUN mode: bind proxy outbound to physical interface to bypass routing (avoid loop)
        if tun_mode and outbound_interface:
            stream["sockopt"] = {"interface": outbound_interface}

        # Build outbound configuration (tag "proxy" for routing)
        outbound = {
            "protocol": protocol,
            "tag": "proxy",
            "settings": settings,
            "streamSettings": stream,
        }

        # Direct outbound for bypassing (private/LAN IPs - geoip:private)
        direct_outbound = {
            "protocol": "freedom",
            "settings": {"domainStrategy": "UseIP"},
            "tag": "direct",
        }

        # Sniffing restores the destination domain so domain-based routing
        # rules work for transparently redirected traffic.
        sniffing = {"enabled": True, "destOverride": ["http", "tls", "quic"]}

        # Build complete config
        config = {
            "log": {"loglevel": "warning"},
            "inbounds": [],
            "outbounds": [outbound, direct_outbound],
        }

        # Routing: private/LAN IPs bypass via direct; everything else falls
        # through to the first outbound (proxy).
        # Requires geoip.dat alongside the xray-core binary (shipped in release).
        routing_rules = [
            # Stats API traffic must be matched before the private-IP bypass
            # (its destination is 127.0.0.1).
            {"type": "field", "inboundTag": ["api"], "outboundTag": "api"},
            # Bypass private/LAN IPs (127.x, 10.x, 192.168.x, etc.)
            {"type": "field", "ip": ["geoip:private"], "outboundTag": "direct"},
            # SOCKS/HTTP inbound traffic goes through proxy
            {
                "type": "field",
                "inboundTag": ["socks", "http"],
                "outboundTag": "proxy",
            },
        ]
        config["routing"] = {
            "domainStrategy": "IPIfNonMatch",
            "rules": routing_rules,
        }

        # Traffic statistics: StatsService on a localhost-only API inbound,
        # queried with `xray api statsquery`.
        config["stats"] = {}
        config["policy"] = {
            "system": {
                "statsOutboundUplink": True,
                "statsOutboundDownlink": True,
            }
        }
        config["api"] = {"tag": "api", "services": ["StatsService"]}
        config["inbounds"].append(
            {
                "listen": "127.0.0.1",
                "port": API_PORT,
                "protocol": "dokodemo-door",
                "settings": {"address": "127.0.0.1"},
                "tag": "api",
            }
        )

        # Always add SOCKS proxy inbound (needed for System Proxy mode)
        # This allows System Proxy to work both with and without TUN mode
        config["inbounds"].append(
            {
                "protocol": "socks",
                "listen": "127.0.0.1",
                "port": 10808,  # Standard SOCKS port, avoids Steam ports
                "settings": {"udp": True},
                "sniffing": sniffing,
                "tag": "socks",
            }
        )

        # Add HTTP proxy inbound (some apps prefer HTTP proxy)
        config["inbounds"].append(
            {
                "protocol": "http",
                "listen": "127.0.0.1",
                "port": 10809,  # HTTP proxy port
                "sniffing": sniffing,
                "tag": "http",
            }
        )

        # Add TUN mode configuration if enabled
        if tun_mode:
            # TUN traffic goes through the proxy — but only AFTER the
            # private-IP bypass above. Rules are first-match: with the TUN
            # rule in front of it, LAN traffic and DNS queries to the home
            # router would be sent into the tunnel and die, killing all
            # connectivity while connected (the original v1 TUN bug,
            # reintroduced when the stats API rule bumped this insert index).
            routing_rules.insert(
                2,
                {"type": "field", "inboundTag": ["tun"], "outboundTag": "proxy"},
            )

            # TUN inbound — supported since xray-core v26.1.23.
            # xray-core creates the TUN interface; no settings required.
            # System routing must still be set up externally (tun_manager).
            config["inbounds"].append(
                {
                    "protocol": "tun",
                    "sniffing": sniffing,
                    "tag": "tun",
                }
            )

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
                # xray-core outputs startup errors to stdout (not stderr),
                # so read both streams to capture the actual error message.
                stderr = await self.process.stderr.read()
                stdout = await self.process.stdout.read()
                stderr_text = stderr.decode("utf-8", errors="ignore").strip() if stderr else ""
                stdout_text = stdout.decode("utf-8", errors="ignore").strip() if stdout else ""
                error_msg = stderr_text or stdout_text or "Unknown error"
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

            # Terminate process (it may already have exited, e.g. after a
            # crash handled by the supervisor — that's not an error).
            try:
                self.process.terminate()
            except ProcessLookupError:
                pass

            # Wait for process to terminate (with timeout)
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                # Force kill if process doesn't terminate
                try:
                    self.process.kill()
                except ProcessLookupError:
                    pass
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
