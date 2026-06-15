"""
Xray downloader - ensures the xray-core binary and geo data files are present.

Why this exists:
SteamOS uses an immutable root filesystem and atomic system updates. The plugin
ships the xray-core binary in its ``bin/`` directory, but on some devices that
binary (and the ``geoip.dat`` / ``geosite.dat`` data files next to it) can be
wiped after a reboot or system update. When that happens the plugin can no
longer start xray-core.

This module re-downloads xray-core + geo data files into a writable, persistent
location (DECKY_PLUGIN_RUNTIME_DIR, the same place TLS certs are stored) whenever
they are missing. The download source mirrors the release workflow
(.github/workflows/release.yml): the official XTLS/Xray-core GitHub releases,
``Xray-linux-64.zip`` for the Steam Deck's x86_64 CPU.

Network calls use the system ``curl`` with a cleaned environment because the
Decky sandbox sets LD_LIBRARY_PATH/LD_PRELOAD to bundled libs that break system
tools (see cert_utils.py for the same approach). Extraction uses the stdlib
``zipfile`` module so no external ``unzip`` is required.
"""

import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional

XRAY_REPO = "XTLS/Xray-core"
XRAY_ASSET = "Xray-linux-64.zip"
BINARY_NAME = "xray-core"
GEO_FILES = ("geoip.dat", "geosite.dat")

# Name of the binary inside the official release archive.
ARCHIVE_BINARY_NAME = "xray"

# Used only when the GitHub API is unreachable (e.g. rate limited / offline).
# Must be a release that supports the TUN inbound (>= v26.1.23, see xray_manager).
FALLBACK_XRAY_VERSION = "v26.1.23"

# Network timeouts (seconds).
_API_TIMEOUT = 20
_DOWNLOAD_TIMEOUT = 300


def _clean_env() -> Dict[str, str]:
    """Environment for system binaries, without the Decky sandbox lib overrides."""
    env = os.environ.copy()
    env.pop("LD_LIBRARY_PATH", None)
    env.pop("LD_PRELOAD", None)
    return env


def binary_present(binary_path: Path) -> bool:
    """True if the xray-core binary exists and is executable."""
    binary_path = Path(binary_path)
    return binary_path.is_file() and os.access(binary_path, os.X_OK)


def geo_files_present(directory: Path) -> bool:
    """True if both geoip.dat and geosite.dat exist in directory."""
    directory = Path(directory)
    return all((directory / name).is_file() for name in GEO_FILES)


def fetch_latest_version() -> Optional[str]:
    """
    Return the latest xray-core release tag (e.g. "v26.1.23"), or None if the
    GitHub API cannot be reached or parsed.
    """
    try:
        result = subprocess.run(
            ["curl", "-sSL", f"https://api.github.com/repos/{XRAY_REPO}/releases/latest"],
            capture_output=True,
            text=True,
            timeout=_API_TIMEOUT,
            env=_clean_env(),
        )
        if result.returncode == 0 and result.stdout:
            tag = json.loads(result.stdout).get("tag_name")
            if tag:
                return str(tag)
    except Exception:
        pass
    return None


def _download_file(url: str, dest: Path) -> bool:
    """Download url to dest using system curl. Returns True on success."""
    try:
        result = subprocess.run(
            ["curl", "-sSL", "-f", "-o", str(dest), url],
            capture_output=True,
            text=True,
            timeout=_DOWNLOAD_TIMEOUT,
            env=_clean_env(),
        )
        return result.returncode == 0 and Path(dest).is_file()
    except Exception:
        return False


def _extract(zip_path: Path, target_dir: Path) -> None:
    """
    Extract the xray binary and geo data files from the release archive into
    target_dir. The binary is renamed from "xray" to BINARY_NAME. Geo files are
    optional (skipped if absent). Raises if the binary is missing.
    """
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())

        if ARCHIVE_BINARY_NAME not in names:
            raise RuntimeError(
                f"'{ARCHIVE_BINARY_NAME}' not found in archive (contents: {sorted(names)})"
            )

        wanted = {ARCHIVE_BINARY_NAME: BINARY_NAME}
        for geo in GEO_FILES:
            if geo in names:
                wanted[geo] = geo

        for member, dest_name in wanted.items():
            with zf.open(member) as src, open(target_dir / dest_name, "wb") as dst:
                shutil.copyfileobj(src, dst)


def download_xray(target_dir: Path, version: Optional[str] = None) -> Dict[str, Any]:
    """
    Download and install xray-core + geo data files into target_dir.

    Args:
        target_dir: Writable directory to install the binary and geo files into.
        version: Release tag to download. If None, the latest release is used
                 (falling back to FALLBACK_XRAY_VERSION when the API is down).

    Returns:
        Result dict with ``success`` and either ``version``/``path`` or
        ``error``/``errorCode``.
    """
    target_dir = Path(target_dir)
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return {
            "success": False,
            "error": f"Cannot create target directory {target_dir}: {e}",
            "errorCode": "TARGET_DIR_ERROR",
        }

    resolved_version = version or fetch_latest_version() or FALLBACK_XRAY_VERSION
    url = (
        f"https://github.com/{XRAY_REPO}/releases/download/"
        f"{resolved_version}/{XRAY_ASSET}"
    )

    tmp_dir = Path(tempfile.mkdtemp(prefix="xray-dl-"))
    try:
        zip_path = tmp_dir / XRAY_ASSET
        if not _download_file(url, zip_path):
            return {
                "success": False,
                "error": f"Failed to download {url}",
                "errorCode": "DOWNLOAD_FAILED",
            }

        try:
            _extract(zip_path, target_dir)
        except (zipfile.BadZipFile, RuntimeError) as e:
            return {
                "success": False,
                "error": f"Failed to extract xray-core archive: {e}",
                "errorCode": "ARCHIVE_INVALID",
            }

        binary_path = target_dir / BINARY_NAME
        os.chmod(binary_path, 0o755)

        return {
            "success": True,
            "version": resolved_version,
            "path": str(binary_path),
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to install xray-core: {e}",
            "errorCode": "DOWNLOAD_ERROR",
        }
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def ensure_xray_binary(
    binary_path: Path, version: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ensure the xray-core binary and geo data files exist next to binary_path.

    If the binary is already present and executable and the geo files are next to
    it, returns success without downloading. Otherwise downloads them into the
    binary's directory.

    Args:
        binary_path: Expected path to the xray-core binary.
        version: Optional release tag to download (defaults to latest).

    Returns:
        Result dict. On success includes ``path``; ``alreadyPresent`` is True when
        no download was needed.
    """
    binary_path = Path(binary_path)
    target_dir = binary_path.parent

    if binary_present(binary_path) and geo_files_present(target_dir):
        return {"success": True, "alreadyPresent": True, "path": str(binary_path)}

    return download_xray(target_dir, version)
