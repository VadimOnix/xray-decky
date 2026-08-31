"""
Xray Manager - Manages xray-core process lifecycle

Handles starting, stopping, and monitoring xray-core subprocess.
Generates xray-core configuration files from VLESSConfig.
"""

import asyncio
import json
import os
import tempfile
from typing import Any, Dict, List, Optional

from .stats import API_PORT


# Steam's Linux client selects CDN endpoints dynamically.  The published
# geosite:steam@cn set does not cover all of the download hosts it returns,
# while store/community must remain on the proxy.  These are download-only
# suffixes observed in Steam's content client logs.
_STEAM_DOWNLOAD_DOMAIN_RULES = (
    "domain:steamcontent.com",
    "domain:steampipe.akamaized.net",
    "domain:steamcdn-a.akamaihd.net",
)


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
        route_rules: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Generate xray-core JSON configuration from VLESSConfig.

        Args:
            vless_config: VLESSConfig dictionary
            tun_mode: Whether to enable TUN mode
            outbound_interface: For TUN mode, bind proxy to this interface (e.g. wlan0)
            route_rules: User-editable routing rules (see backend.src.route_rules).
                Read on every call so an updated ruleset is reflected on the
                next generated config without restarting the proxy.

        Returns:
            Path to generated config file
        """
        # Create temporary config file
        config_dir = tempfile.gettempdir()
        config_file = os.path.join(config_dir, f"xray-config-{os.getpid()}.json")

        # Generate xray-core config
        xray_config = self._build_xray_config(
            vless_config, tun_mode, outbound_interface, route_rules=route_rules
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
        route_rules: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Build xray-core JSON configuration structure.

        Args:
            vless_config: Profile dictionary (see config_parser.parse_share_link);
                profiles imported before multi-protocol support lack the
                "protocol" key and default to VLESS.
            tun_mode: Whether to enable TUN mode
            route_rules: User-editable routing rules (see route_rules.py).
                Inserted after the LAN bypass so user rules can never wedge
                LAN traffic into the tunnel. Each rule is
                ``{"id", "enabled", "action", "match": {"type", "value"}}``.

        Returns:
            xray-core configuration dictionary
        """
        if route_rules is None:
            route_rules = []
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
        elif protocol == "hysteria2":
            # xray-core >= v26.7.28 supports the Hysteria2 client natively
            # (upstream PR #6198). The JSON config has two pieces:
            #   - outbound.settings  = {version, address, port}        (HysteriaClientConfig)
            #   - streamSettings.hysteriaSettings = {version, auth, ...} (HysteriaConfig in transport_method.go)
            # The auth (password) lives in the transport-level config — without
            # that block the hysteria client refuses to start with
            # "not hysteria transport" because its config comes from the
            # stream's ProtocolSettings, not from the outbound's settings.
            settings = {
                "version": 2,
                "address": address,
                "port": port,
            }
            # Marked for the post-stream splice below (see _attach_hysteria_stream).
            settings["_hysteria_auth"] = vless_config.get("password", "")
            # Hysteria2 mandates udp+tls; the share-link parser already sets
            # network="udp" and security="tls".
            obfs_type = vless_config.get("obfs")
            if obfs_type:
                salamander: Dict[str, Any] = {"password": vless_config.get("obfsPassword") or ""}
                if vless_config.get("geckoEnabled") or str(obfs_type).lower() == "gecko":
                    # Gecko (Hysteria v2.9.2): random-length UDP packet padding
                    # via the salamander finalmask's packetSize range. xray-core's
                    # Int32Range type accepts either a plain int or a "min-max"
                    # string (e.g. "1000-1500"); it does NOT accept a {from, to}
                    # object — see infra/conf/transport_finalmask.go Salamander.
                    salamander["packetSize"] = "1000-1500"
                # Will be spliced into streamSettings below — see _attach_finalmask.
                settings["_finalmask"] = {
                    "udp": [{"type": "salamander", "settings": salamander}]
                }
        elif protocol == "socks":
            server: Dict[str, Any] = {"address": address, "port": port}
            username = vless_config.get("username")
            if username:
                server["users"] = [
                    {"user": username, "pass": vless_config.get("password") or ""}
                ]
            settings = {"servers": [server]}
            # Plain SOCKS5 has no transport security of its own; forcing
            # tcp/none keeps a mislabelled profile from attempting a TLS
            # handshake the proxy cannot answer.
            network = "tcp"
            security = "none"
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
            elif protocol == "hysteria2":
                # Native Hysteria is HTTP/3 over QUIC; without h3 in the TLS
                # ALPN list the process can stay alive while every request
                # fails during the upstream handshake.
                tls_settings["alpn"] = ["h3"]
            if tls_config.get("fingerprint") and protocol != "hysteria2":
                tls_settings["fingerprint"] = tls_config["fingerprint"]
            # Xray v26.7.28 removed allowInsecure from TLSConfig. Keep the
            # legacy profile flag for sing-box/export compatibility, but never
            # put it in an Xray config: the core rejects it before startup.
            if tls_config.get("pinnedPeerCertSha256"):
                tls_settings["pinnedPeerCertSha256"] = tls_config[
                    "pinnedPeerCertSha256"
                ]
            if tls_config.get("verifyPeerCertByName"):
                tls_settings["verifyPeerCertByName"] = tls_config[
                    "verifyPeerCertByName"
                ]
            if tls_config.get("echConfigList"):
                tls_settings["echConfigList"] = tls_config["echConfigList"]
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

        # Hysteria2-specific hooks (see _parse_hysteria2 branch above):
        # - Hysteria2 runs over QUIC/UDP, but its Xray stream transport is the
        #   dedicated `hysteria` protocol. `udp` is not a valid value for
        #   streamSettings.network in Xray v26.7.28 and produces:
        #     "infra/conf: Config: unknown transport protocol: udp".
        # - The salamander / gecko finalmask is opt-in via obfs and stays in
        #   streamSettings.finalmask, where it is documented as the right home.
        if protocol == "hysteria2":
            # The native Xray Hysteria client expects the dedicated transport
            # name here; omitting it leaves the stream on tcp, while using udp
            # is rejected by TransportProtocol.Build().
            stream["network"] = "hysteria"
            # The Hysteria auth lives in the stream transport block. Without
            # this, the proxy/hysteria client aborts with "not hysteria
            # transport" because it looks up its config from the stream's
            # ProtocolSettings (a *hysteria.Config), not from the outbound.
            auth = settings.pop("_hysteria_auth", None)
            if auth is not None:
                stream["hysteriaSettings"] = {"version": 2, "auth": auth}
            finalmask = settings.pop("_finalmask", None)
            port_hopping = vless_config.get("portHopping")
            if isinstance(port_hopping, dict) and port_hopping.get("ports"):
                if finalmask is None:
                    finalmask = {}
                finalmask["quicParams"] = {
                    "udpHop": {
                        "ports": str(port_hopping["ports"]),
                        "interval": str(port_hopping.get("interval") or "30"),
                    }
                }
            if finalmask is not None:
                stream["finalmask"] = finalmask

        # TUN mode: bind proxy outbound to physical interface to bypass routing (avoid loop)
        if tun_mode and outbound_interface:
            stream["sockopt"] = {"interface": outbound_interface}

        # Build outbound configuration (tag "proxy" for routing).
        # xray-core registers the Hysteria v1+v2 client under the outbound id
        # "hysteria" (v1/v2 is distinguished by settings.version, not by name).
        outbound_protocol = "hysteria" if protocol == "hysteria2" else protocol
        outbound = {
            "protocol": outbound_protocol,
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
        if tun_mode and outbound_interface:
            # The system default route points at xray0 in TUN mode. Direct
            # traffic must leave through the physical interface as well, or
            # freedom follows the TUN route and loops back into this core.
            direct_outbound["streamSettings"] = {
                "sockopt": {"interface": outbound_interface}
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
            # Bypass private/LAN IPs (127.x, 10.x, 192.168.x, etc.) — MUST stay
            # ahead of any user rule that could otherwise funnel LAN traffic
            # into the tunnel.
            {"type": "field", "ip": ["geoip:private"], "outboundTag": "direct"},
        ]
        direct_dns_domains: List[str] = []
        # User-editable rules (configurable via the admin panel). Disabled
        # rules are skipped here but kept on disk so users can re-enable them.
        for rule in route_rules:
            if not rule.get("enabled", True):
                continue
            action = rule.get("action")
            target = {
                "proxy": "proxy",
                "direct": "direct",
                "reject": "block",
            }.get(action)
            if target is None:
                continue
            match = rule.get("match") or {}
            m_type = match.get("type")
            value = match.get("value", "")
            domains = [value]
            if (
                target == "direct"
                and m_type == "geosite"
                and value.lower() == "geosite:steam@cn"
            ):
                # Keep the fallback in the same first-match rule as the
                # user's geosite rule. This preserves the rule's position and
                # does not make store.steampowered.com or
                # steamcommunity.com direct.
                domains.extend(_STEAM_DOWNLOAD_DOMAIN_RULES)
            if target == "direct" and m_type in ("domain", "geosite") and value:
                direct_dns_domains.extend(domains)
            if m_type == "domain":
                routing_rules.append({"type": "field", "domain": domains, "outboundTag": target})
            elif m_type == "ip":
                routing_rules.append({"type": "field", "ip": [value], "outboundTag": target})
            elif m_type == "geosite":
                routing_rules.append({"type": "field", "domain": domains, "outboundTag": target})
            elif m_type == "geoip":
                routing_rules.append({"type": "field", "ip": [value], "outboundTag": target})

        if tun_mode:
            # Native Xray TUN does not otherwise see the DNS query that Steam
            # sends to the system resolver. Hijack port 53 into Xray's DNS
            # outbound so transparent connections can retain a routeable
            # domain instead of becoming an IP-only connection.
            routing_rules.insert(
                1,
                {
                    "type": "field",
                    "inboundTag": ["tun"],
                    "port": 53,
                    "outboundTag": "dns-out",
                },
            )
            config["outbounds"].append({"protocol": "dns", "tag": "dns-out"})
            config["dns"] = {
                "servers": ["localhost"],
                "queryStrategy": "UseIPv4",
            }

            # FakeDNS is deliberately limited to user-selected direct domain
            # rules. It preserves the domain across an IP-only TUN connection
            # (Steam downloads are the main example) without changing the
            # normal proxy treatment of store/community domains.
            if direct_dns_domains:
                config["dns"]["servers"].insert(
                    0,
                    {"address": "fakedns", "domains": direct_dns_domains},
                )
                config["fakedns"] = {
                    "ipPool": "198.18.0.0/15",
                    "poolSize": 65535,
                }
                sniffing["destOverride"].append("fakedns")

        # Built-in inbound-to-outbound fall-through rules.
        routing_rules.extend(
            [
                # SOCKS/HTTP inbound traffic goes through proxy
                {
                    "type": "field",
                    "inboundTag": ["socks", "http"],
                    "outboundTag": "proxy",
                },
            ]
        )
        config["routing"] = {
            "domainStrategy": "IPIfNonMatch",
            "rules": routing_rules,
        }

        # Blackhole outbound is only added when at least one user rule asks for
        # reject; avoids an unused outbound in the common case.
        if any(r.get("enabled", True) and r.get("action") == "reject" for r in route_rules):
            config["outbounds"].append(
                {"protocol": "blackhole", "tag": "block"}
            )

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
            # TUN traffic falls through to the proxy only after user rules.
            # Rules are first-match: putting this catch-all before a user
            # geosite/domain rule makes direct or reject rules ineffective
            # for every TUN connection (Steam downloads included).
            routing_rules.append(
                {"type": "field", "inboundTag": ["tun"], "outboundTag": "proxy"}
            )

            # TUN inbound — supported since xray-core v26.1.23. Explicitly
            # name the interface because tun_manager waits for xray0 before
            # adding the system route. Without this, Xray chooses its own
            # platform-dependent name (for example utunN), so route setup
            # races against an interface that will never appear.
            # System routing must still be set up externally (tun_manager).
            config["inbounds"].append(
                {
                    "protocol": "tun",
                    "settings": {"name": "xray0", "mtu": 1500},
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
