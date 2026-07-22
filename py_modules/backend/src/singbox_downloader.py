"""
sing-box downloader — fetches the sing-box binary on demand.

The sing-box core (Hysteria2 / TUIC) is downloaded into a writable,
persistent location (DECKY_PLUGIN_RUNTIME_DIR) the first time it is needed,
rather than bundled in the plugin zip, to keep the store package small.

Mirrors xray_downloader (pinned version JSON, optional sha256, cleaned
environment for system curl) but for sing-box's ``.tar.gz`` release layout:
the archive contains ``sing-box-<version>-linux-amd64/sing-box``.
"""

import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

SINGBOX_REPO = "SagerNet/sing-box"
BINARY_NAME = "sing-box"
# Name of the binary inside the official release archive.
ARCHIVE_BINARY_NAME = "sing-box"

_VERSION_FILE = Path(__file__).resolve().parent / "singbox_version.json"
FALLBACK_SINGBOX_VERSION = "v1.11.15"
_DEFAULT_ASSET = "sing-box-{version_no_v}-linux-amd64.tar.gz"

_DOWNLOAD_TIMEOUT = 300


def _load_pin() -> Dict[str, Any]:
    """Read the pinned metadata; empty dict on any problem (incl. non-object)."""
    try:
        with open(_VERSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def pinned_version() -> str:
    """The pinned sing-box release tag, or the hardcoded fallback."""
    return str(_load_pin().get("version") or FALLBACK_SINGBOX_VERSION)


def pinned_repo() -> str:
    """The GitHub repo the pinned sing-box release is fetched from."""
    return str(_load_pin().get("repo") or SINGBOX_REPO)


def pinned_sha256() -> Optional[str]:
    """Expected sha256 of the release asset, or None when unset."""
    value = _load_pin().get("sha256")
    return str(value).lower() if value else None


def _resolve_asset(asset_template: str, version: str) -> str:
    """Fill the {version_no_v} placeholder in an asset name."""
    version_no_v = version[1:] if version.startswith("v") else version
    return asset_template.replace("{version_no_v}", version_no_v)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _clean_env() -> Dict[str, str]:
    env = os.environ.copy()
    env.pop("LD_LIBRARY_PATH", None)
    env.pop("LD_PRELOAD", None)
    return env


def binary_present(binary_path: Path) -> bool:
    """True if the sing-box binary exists and is executable."""
    binary_path = Path(binary_path)
    return binary_path.is_file() and os.access(binary_path, os.X_OK)


def _download_file(url: str, dest: Path) -> bool:
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


def _extract(tar_path: Path, target_dir: Path) -> None:
    """
    Extract the sing-box binary from the release tarball into target_dir.

    The binary lives at ``<something>/sing-box`` inside the archive; it is
    written to ``target_dir/sing-box``. Raises if the binary is absent.
    """
    with tarfile.open(tar_path, "r:gz") as tf:
        member = None
        for candidate in tf.getmembers():
            if candidate.isfile() and os.path.basename(candidate.name) == (
                ARCHIVE_BINARY_NAME
            ):
                member = candidate
                break
        if member is None:
            names = [m.name for m in tf.getmembers()]
            raise RuntimeError(
                f"'{ARCHIVE_BINARY_NAME}' not found in archive (contents: {names})"
            )
        src = tf.extractfile(member)
        if src is None:
            raise RuntimeError("Could not read sing-box binary from archive")
        with src, open(target_dir / BINARY_NAME, "wb") as dst:
            shutil.copyfileobj(src, dst)


def download_singbox(
    target_dir: Path, version: Optional[str] = None
) -> Dict[str, Any]:
    """
    Download and install the sing-box binary into target_dir.

    Args:
        target_dir: Writable directory to install the binary into.
        version: Release tag to download. If None, the pinned version is used.

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

    pin = _load_pin()
    repo = pin.get("repo") or SINGBOX_REPO
    asset_template = pin.get("asset") or _DEFAULT_ASSET
    resolved_version = version or pin.get("version") or FALLBACK_SINGBOX_VERSION
    asset = _resolve_asset(asset_template, resolved_version)

    # Only verify the pinned checksum when downloading the pinned version.
    expected_sha = None
    if version is None:
        sha = pin.get("sha256")
        expected_sha = str(sha).lower() if sha else None

    url = f"https://github.com/{repo}/releases/download/{resolved_version}/{asset}"

    tmp_dir = Path(tempfile.mkdtemp(prefix="singbox-dl-"))
    try:
        tar_path = tmp_dir / asset
        if not _download_file(url, tar_path):
            return {
                "success": False,
                "error": f"Failed to download {url}",
                "errorCode": "DOWNLOAD_FAILED",
            }

        if expected_sha:
            actual_sha = _sha256(tar_path)
            if actual_sha != expected_sha:
                return {
                    "success": False,
                    "error": (
                        f"Checksum mismatch for {asset}: "
                        f"expected {expected_sha}, got {actual_sha}"
                    ),
                    "errorCode": "CHECKSUM_MISMATCH",
                }

        try:
            _extract(tar_path, target_dir)
        except (tarfile.TarError, RuntimeError) as e:
            return {
                "success": False,
                "error": f"Failed to extract sing-box archive: {e}",
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
            "error": f"Failed to install sing-box: {e}",
            "errorCode": "DOWNLOAD_ERROR",
        }
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def ensure_singbox_binary(
    binary_path: Path, version: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ensure the sing-box binary exists at binary_path, downloading if missing.

    Returns a result dict; ``alreadyPresent`` is True when no download ran.
    """
    binary_path = Path(binary_path)
    if binary_present(binary_path):
        return {"success": True, "alreadyPresent": True, "path": str(binary_path)}
    return download_singbox(binary_path.parent, version)
