"""
sing-box configuration generator (second core for Hysteria2 / TUIC).

Turns a parsed profile (config_parser, ``core == "sing-box"``) into a
sing-box JSON config. Kept parallel to xray_manager: the same localhost
SOCKS/HTTP inbound ports (10808/10809) and TUN interface (xray0) so the
existing system-proxy, kill-switch and routing paths are reused whichever
core is active.

This module is the config substrate for the sing-box core. Process
lifecycle wiring into the connect path is a separate step.
"""

import json
import os
import tempfile
from typing import Any, Dict, Optional

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
) -> Dict[str, Any]:
    """
    Build a sing-box JSON configuration for a hysteria2/tuic profile.

    Args:
        profile: Parsed profile with ``core == "sing-box"``.
        tun_mode: Whether to add the TUN inbound (system-wide routing).
        outbound_interface: Physical interface to bind the proxy outbound to
            in TUN mode, so proxy traffic bypasses the tunnel (avoids a loop).

    Returns:
        sing-box configuration dictionary.
    """
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
                "stack": "system",
                # System routing is set up externally (tun_manager), matching
                # the xray path — don't let sing-box manage routes itself.
                "auto_route": False,
            }
        )

    config: Dict[str, Any] = {
        "log": {"level": "warn"},
        "inbounds": inbounds,
        "outbounds": [
            proxy,
            {"type": "direct", "tag": "direct"},
        ],
        "route": {
            # Private/LAN IPs bypass the proxy; everything else goes to proxy.
            "rules": [{"ip_is_private": True, "outbound": "direct"}],
            "final": "proxy",
        },
    }
    return config


class SingBoxManager:
    """
    Generates sing-box configs and manages the sing-box subprocess.

    Parallel to XrayManager. Process start/stop is provided so the core is
    ready to wire into the connect path; that wiring is a separate step.
    """

    def __init__(self, binary_path: str = "backend/out/sing-box") -> None:
        self.binary_path = binary_path
        self.config_file: Optional[str] = None
        self.process = None
        self.process_id: Optional[int] = None

    def generate_config(
        self,
        profile: Dict[str, Any],
        tun_mode: bool = False,
        outbound_interface: Optional[str] = None,
    ) -> str:
        """Write a sing-box config to a temp file and return its path."""
        config_dir = tempfile.gettempdir()
        config_file = os.path.join(config_dir, f"singbox-config-{os.getpid()}.json")
        config = build_singbox_config(profile, tun_mode, outbound_interface)
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        self.config_file = config_file
        return config_file
