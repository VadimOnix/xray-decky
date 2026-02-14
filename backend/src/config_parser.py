"""
VLESS Configuration Parser

Parses and validates VLESS URLs (single node or subscription).
"""

import re
import base64
import json
import urllib.parse
from typing import Dict, Any, Optional, List
from uuid import UUID


# VLESS URL pattern: vless://uuid@host:port?params#name
VLESS_URL_PATTERN = re.compile(
    r"^vless://([a-f0-9-]{36})@([^:]+):(\d+)(\?[^#]*)?(#.*)?$", re.IGNORECASE
)


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate UUID v4 format.

    Args:
        uuid_string: UUID string to validate

    Returns:
        True if valid UUID v4, False otherwise
    """
    try:
        uuid_obj = UUID(uuid_string, version=4)
        return str(uuid_obj).lower() == uuid_string.lower()
    except (ValueError, AttributeError):
        return False


def validate_port(port: int) -> bool:
    """
    Validate port number.

    Args:
        port: Port number to validate

    Returns:
        True if port is in valid range (1-65535), False otherwise
    """
    try:
        port_int = int(port)
        return 1 <= port_int <= 65535
    except (ValueError, TypeError):
        return False


def validate_hostname(hostname: str) -> bool:
    """
    Basic hostname/IP validation.

    Args:
        hostname: Hostname or IP address to validate

    Returns:
        True if hostname looks valid, False otherwise
    """
    if not hostname or len(hostname) > 253:
        return False

    # Basic IP address validation (IPv4)
    ipv4_pattern = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
    if ipv4_pattern.match(hostname):
        parts = hostname.split(".")
        return all(0 <= int(part) <= 255 for part in parts)

    # Basic hostname validation (simplified)
    hostname_pattern = re.compile(
        r"^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?)*$",
        re.IGNORECASE,
    )
    return bool(hostname_pattern.match(hostname))


def parse_vless_url(url: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single VLESS URL into components.

    Args:
        url: VLESS URL string (vless://uuid@host:port?params#name)

    Returns:
        Dictionary with parsed components, or None if invalid
    """
    match = VLESS_URL_PATTERN.match(url.strip())
    if not match:
        return None

    uuid_str = match.group(1)
    host = match.group(2)
    port_str = match.group(3)
    params_str = match.group(4) or ""
    name_fragment = match.group(5) or ""

    # Validate UUID
    if not validate_uuid(uuid_str):
        return None

    # Validate port
    try:
        port = int(port_str)
        if not validate_port(port):
            return None
    except ValueError:
        return None

    # Validate hostname
    if not validate_hostname(host):
        return None

    # Parse query parameters
    params = {}
    if params_str.startswith("?"):
        params_str = params_str[1:]

    if params_str:
        for param in params_str.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                params[urllib.parse.unquote(key)] = urllib.parse.unquote(value)

    # Extract name from fragment
    name = None
    if name_fragment.startswith("#"):
        name = urllib.parse.unquote(name_fragment[1:])

    return {
        "uuid": uuid_str.lower(),
        "address": host,
        "port": port,
        "params": params,
        "name": name,
    }


def parse_subscription_url(url: str) -> List[Dict[str, Any]]:
    """
    Parse a subscription URL (base64-encoded JSON array).

    Args:
        url: Base64-encoded JSON array of VLESS URLs

    Returns:
        List of parsed VLESS configurations, empty list if invalid
    """
    try:
        # Decode base64
        decoded_bytes = base64.b64decode(url)
        decoded_str = decoded_bytes.decode("utf-8")

        # Parse JSON
        configs = json.loads(decoded_str)

        if not isinstance(configs, list):
            return []

        # Parse each VLESS URL in the array
        parsed_configs = []
        for config_url in configs:
            if isinstance(config_url, str):
                parsed = parse_vless_url(config_url)
                if parsed:
                    parsed_configs.append(parsed)

        return parsed_configs
    except (base64.binascii.Error, json.JSONDecodeError, UnicodeDecodeError, TypeError):
        return []


def validate_vless_url(url: str) -> tuple[bool, Optional[str]]:
    """
    Validate a VLESS URL (single node or subscription).

    Args:
        url: VLESS URL to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "Invalid URL format"

    url = url.strip()

    # Try parsing as single node first
    parsed = parse_vless_url(url)
    if parsed:
        return True, None

    # Try parsing as subscription
    parsed_configs = parse_subscription_url(url)
    if parsed_configs:
        return True, None

    # If neither works, return error
    return (
        False,
        "Invalid VLESS URL format. Expected vless://uuid@host:port?params#name or base64 subscription",
    )


def build_vless_config(
    parsed: Dict[str, Any], source_url: str, config_type: str
) -> Dict[str, Any]:
    """
    Build a complete VLESSConfig dictionary from parsed components.

    Args:
        parsed: Parsed URL components
        source_url: Original source URL
        config_type: 'single' or 'subscription'

    Returns:
        Complete VLESSConfig dictionary
    """
    import time

    config = {
        "sourceUrl": source_url,
        "configType": config_type,
        "uuid": parsed["uuid"],
        "address": parsed["address"],
        "port": parsed["port"],
        "importedAt": int(time.time()),
        "isValid": True,
    }

    # Extract optional fields from params
    params = parsed.get("params", {})
    if "flow" in params:
        config["flow"] = params["flow"]
    if "encryption" in params:
        config["encryption"] = params["encryption"]
    if "type" in params or "network" in params:
        config["network"] = params.get("type") or params.get("network")
    if "security" in params:
        config["security"] = params["security"]

    # Extract Reality-specific fields
    if config.get("security") == "reality":
        reality_config = {}
        if "pbk" in params or "publicKey" in params:
            reality_config["publicKey"] = params.get("pbk") or params.get("publicKey")
        if "sid" in params or "shortId" in params:
            reality_config["shortId"] = params.get("sid") or params.get("shortId")
        if "sni" in params or "serverName" in params:
            reality_config["serverName"] = params.get("sni") or params.get("serverName")
        if "fp" in params or "fingerprint" in params:
            reality_config["fingerprint"] = params.get("fp") or params.get(
                "fingerprint"
            )

        if reality_config:
            config["realityConfig"] = reality_config

    # Extract name
    if parsed.get("name"):
        config["name"] = parsed["name"]

    return config
