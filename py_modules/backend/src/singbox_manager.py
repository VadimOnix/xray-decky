"""
sing-box configuration generator (second core for Hysteria2 / TUIC).

Turns a parsed profile (config_parser, ``core == "sing-box"``) into a
sing-box JSON config. Kept parallel to xray_manager: the same localhost
SOCKS/HTTP inbound ports (10808/10809) and TUN interface (xray0) so the
existing system-proxy, kill-switch and routing paths are reused whichever
core is active.

Process lifecycle mirrors XrayManager so main.py can drive either core
through the same start/stop/is_running surface.
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from .singbox_rules import rule_set_definitions, rule_set_tag

SOCKS_PORT = 10808
HTTP_PORT = 10809
TUN_INTERFACE = "xray0"


def _tls_block(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Build the sing-box tls object from a profile's tlsConfig."""
    tls_config = profile.get("tlsConfig") or {}
    tls: Dict[str, Any] = {"enabled": True}
    server_name = tls_config.get("serverName") or profile.get("address")
    if server_name:
        tls["server_name"] = server_name
    if tls_config.get("alpn"):
        tls["alpn"] = tls_config["alpn"]
    if tls_config.get("allowInsecure"):
        tls["insecure"] = True
    return tls


def _proxy_outbound(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Build the sing-box proxy outbound for a hysteria2/tuic profile."""
    protocol = profile.get("protocol")
    address = profile.get("address")
    port = profile.get("port")

    if protocol == "hysteria2":
        outbound: Dict[str, Any] = {
            "type": "hysteria2",
            "tag": "proxy",
            "server": address,
            "server_port": port,
            "password": profile.get("password", ""),
            "tls": _tls_block(profile),
        }
        if profile.get("obfs"):
            outbound["obfs"] = {
                "type": profile["obfs"],
                "password": profile.get("obfsPassword", ""),
            }
        return outbound

    if protocol == "tuic":
        outbound = {
            "type": "tuic",
            "tag": "proxy",
            "server": address,
            "server_port": port,
            "uuid": profile.get("uuid", ""),
            "password": profile.get("password", ""),
            "tls": _tls_block(profile),
        }
        if profile.get("congestionControl"):
            outbound["congestion_control"] = profile["congestionControl"]
        if profile.get("udpRelayMode"):
            outbound["udp_relay_mode"] = profile["udpRelayMode"]
        return outbound

    raise ValueError(f"Unsupported sing-box protocol: {protocol}")


def build_singbox_config(
    profile: Dict[str, Any],
    tun_mode: bool = False,
    outbound_interface: Optional[str] = None,
    route_rules: Optional[List[Dict[str, Any]]] = None,
    rule_set_dir: Optional[Path | str] = None,
) -> Dict[str, Any]:
    """
    Build a sing-box JSON configuration for a hysteria2/tuic profile.

    Args:
        profile: Parsed profile with ``core == "sing-box"``.
        tun_mode: Whether to add the TUN inbound (system-wide routing).
        outbound_interface: Physical interface to bind the proxy outbound to
            in TUN mode, so proxy traffic bypasses the tunnel (avoids a loop).
        route_rules: User-editable routing rules (see backend.src.route_rules).
            Applied between the LAN bypass and the catch-all ``final``.
        rule_set_dir: Directory containing the local binary ``.srs`` files.
            When omitted, use the package-local ``srss`` directory; the main
            runtime passes the packaged or repaired absolute directory.

    Returns:
        sing-box configuration dictionary.
    """
    if route_rules is None:
        route_rules = []
    proxy = _proxy_outbound(profile)
    if tun_mode and outbound_interface:
        proxy["bind_interface"] = outbound_interface

    inbounds = [
        {
            "type": "socks",
            "tag": "socks-in",
            "listen": "127.0.0.1",
            "listen_port": SOCKS_PORT,
        },
        {
            "type": "http",
            "tag": "http-in",
            "listen": "127.0.0.1",
            "listen_port": HTTP_PORT,
        },
    ]
    if tun_mode:
        inbounds.append(
            {
                "type": "tun",
                "tag": "tun-in",
                "interface_name": TUN_INTERFACE,
                # Unlike xray, sing-box has no implicit TUN address; without
                # one the interface can't come up and tun_manager's
                # `ip route add default dev xray0` fails.
                "address": ["172.19.0.1/30"],
                "stack": "system",
                # System routing is set up externally (tun_manager), matching
                # the xray path — don't let sing-box manage routes itself.
                "auto_route": False,
            }
        )

    # Build route.rules in the right order. Order matters in sing-box:
    # first-match wins, so the LAN safety bypass MUST sit ahead of user rules.
    rules: List[Dict[str, Any]] = [
        {"ip_is_private": True, "outbound": "direct"},
    ]
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
        if m_type == "domain":
            rules.append({"domain": [value], "outbound": target})
        elif m_type == "ip":
            rules.append({"ip_cidr": [value], "outbound": target})
        elif m_type == "geosite":
            rules.append({"rule_set": [rule_set_tag(value)], "outbound": target})
        elif m_type == "geoip":
            rules.append({"rule_set": [rule_set_tag(value)], "outbound": target})

    # Outbound "block" is built-in in sing-box, so we don't need to add one.
    direct: Dict[str, Any] = {"type": "direct", "tag": "direct"}
    if tun_mode and outbound_interface:
        # The TUN manager installs xray0 as the preferred default route. A
        # direct connection must bind to the physical interface or it loops
        # back into the sing-box TUN inbound instead of reaching the network.
        direct["bind_interface"] = outbound_interface

    outbounds: List[Dict[str, Any]] = [proxy, direct]

    config: Dict[str, Any] = {
        "log": {"level": "warn"},
        "inbounds": inbounds,
        "outbounds": outbounds,
        "route": {
            "rules": rules,
            "rule_set": rule_set_definitions(
                rule_set_dir
                or Path(__file__).resolve().parent / "srss"
            ),
            "final": "proxy",
        },
    }
    return config


class SingBoxManager:
    """
    Generates sing-box configs and manages the sing-box subprocess.

    Parallel to XrayManager: the same generate_config/start/stop/is_running
    surface, so the connect path in main.py can drive whichever core the
    active profile needs. The process is spawned with an argv vector via
    create_subprocess_exec — no shell is ever involved.
    """

    def __init__(
        self,
        binary_path: str = "backend/out/sing-box",
        rule_set_dir: Optional[Path | str] = None,
    ) -> None:
        self.binary_path = binary_path
        self.rule_set_dir = str(Path(rule_set_dir).expanduser().resolve()) if rule_set_dir else None
        self.config_file: Optional[str] = None
        self.process: Optional[asyncio.subprocess.Process] = None
        self.process_id: Optional[int] = None

    def generate_config(
        self,
        profile: Dict[str, Any],
        tun_mode: bool = False,
        outbound_interface: Optional[str] = None,
        route_rules: Optional[List[Dict[str, Any]]] = None,
        rule_set_dir: Optional[Path | str] = None,
    ) -> str:
        """Write a sing-box config to a temp file and return its path.

        ``route_rules`` is threaded through to :func:`build_singbox_config` so
        a PUT to the admin API is reflected on the next generated config.
        """
        config_dir = tempfile.gettempdir()
        config_file = os.path.join(config_dir, f"singbox-config-{os.getpid()}.json")
        selected_rule_set_dir = rule_set_dir or self.rule_set_dir
        config = build_singbox_config(
            profile,
            tun_mode,
            outbound_interface,
            route_rules=route_rules,
            rule_set_dir=selected_rule_set_dir,
        )
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        self.config_file = config_file
        if selected_rule_set_dir:
            self.rule_set_dir = str(
                Path(selected_rule_set_dir).expanduser().resolve()
            )
        return config_file

    async def start(self, config_file: str) -> Dict[str, Any]:
        """
        Start the sing-box process with the given config file.

        Returns:
            {"success": bool, "processId": int} or {"success": False,
            "error": str, "errorCode": str} — same shape as XrayManager.start.
        """
        try:
            if not os.path.exists(self.binary_path):
                return {
                    "success": False,
                    "error": f"sing-box binary not found at {self.binary_path}",
                    "errorCode": "BINARY_NOT_FOUND",
                }
            if not os.access(self.binary_path, os.X_OK):
                return {
                    "success": False,
                    "error": f"sing-box binary is not executable: {self.binary_path}",
                    "errorCode": "BINARY_NOT_EXECUTABLE",
                }

            self.process = await asyncio.create_subprocess_exec(
                self.binary_path,
                "run",
                "-c",
                config_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self.process_id = self.process.pid
            self.config_file = config_file

            # Give it a moment to fail fast on a bad config/port conflict.
            await asyncio.sleep(0.5)

            if self.process.returncode is not None:
                stderr = await self.process.stderr.read()
                stdout = await self.process.stdout.read()
                stderr_text = (
                    stderr.decode("utf-8", errors="ignore").strip() if stderr else ""
                )
                stdout_text = (
                    stdout.decode("utf-8", errors="ignore").strip() if stdout else ""
                )
                error_msg = stderr_text or stdout_text or "Unknown error"
                return {
                    "success": False,
                    "error": f"sing-box process failed to start: {error_msg}",
                    "errorCode": "PROCESS_START_FAILED",
                }

            return {"success": True, "processId": self.process_id}
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start sing-box: {str(e)}",
                "errorCode": "PROCESS_START_ERROR",
            }

    async def stop(self) -> Dict[str, Any]:
        """Stop the sing-box process and remove its temp config file."""
        try:
            if self.process is None:
                return {"success": True, "message": "No process running"}

            # It may already have exited (e.g. crash handled by the
            # supervisor) — that's not an error.
            try:
                self.process.terminate()
            except ProcessLookupError:
                pass

            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                try:
                    self.process.kill()
                except ProcessLookupError:
                    pass
                await self.process.wait()

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
                "error": f"Failed to stop sing-box: {str(e)}",
                "errorCode": "PROCESS_STOP_ERROR",
            }

    def is_running(self) -> bool:
        """True while the sing-box process is alive."""
        if self.process is None:
            return False
        return self.process.returncode is None

    def get_process_id(self) -> Optional[int]:
        """PID of the running sing-box process, or None."""
        return self.process_id
