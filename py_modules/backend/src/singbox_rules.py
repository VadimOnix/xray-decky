"""Shared manifest and downloader for sing-box binary rule sets.

The WebAdmin and both runtime/package paths use the same ordered manifest so a
route rule can never refer to a tag that was not staged or repaired locally.
The files are the binary ``.srs`` rule sets published by the v2rayN project
under its sing-box-rules mirror.
"""

import os
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, List

from .net_env import clean_subprocess_env


_RULES_BASE_URL = "https://raw.githubusercontent.com/2dust/sing-box-rules"

GEOIP_FILES = (
    "geoip-cn.srs",
    "geoip-facebook.srs",
    "geoip-fastly.srs",
    "geoip-google.srs",
    "geoip-netflix.srs",
    "geoip-private.srs",
    "geoip-telegram.srs",
    "geoip-twitter.srs",
)

GEOSITE_FILES = (
    "geosite-category-ads-all.srs",
    "geosite-category-games@cn.srs",
    "geosite-cn.srs",
    # v2rayN/sing-box-rules also publishes the inverse geo-location set.  It
    # is useful for the existing preset and exercises the real `!` suffix.
    "geosite-geolocation-!cn.srs",
    "geosite-geolocation-cn.srs",
    "geosite-gfw.srs",
    "geosite-google.srs",
    "geosite-greatfire.srs",
    "geosite-private.srs",
    "geosite-steam@cn.srs",
    "geosite-xbox@cn.srs",
)

RULE_SET_FILES = GEOIP_FILES + GEOSITE_FILES

RULE_SET_SOURCES = {
    filename: f"{_RULES_BASE_URL}/rule-set-geoip/{filename}"
    for filename in GEOIP_FILES
}
RULE_SET_SOURCES.update(
    {
        filename: f"{_RULES_BASE_URL}/rule-set-geosite/{filename}"
        for filename in GEOSITE_FILES
    }
)


def rule_set_tag(value: str) -> str:
    """Convert ``geosite:foo``/``geoip:foo`` to its local rule-set tag."""
    if not isinstance(value, str):
        raise ValueError("rule-set value must be a string")
    if value.startswith("geosite:") or value.startswith("geoip:"):
        kind, suffix = value.split(":", 1)
        if not suffix:
            raise ValueError("rule-set value must include a category")
        return f"{kind}-{suffix}"
    raise ValueError(f"unsupported rule-set value: {value!r}")


def rule_set_definitions(directory: Path | str) -> List[Dict[str, str]]:
    """Return sing-box local binary rule-set definitions for ``directory``."""
    rule_dir = Path(directory).expanduser().resolve()
    return [
        {
            "type": "local",
            "tag": Path(filename).stem,
            "format": "binary",
            "path": str(rule_dir / filename),
        }
        for filename in RULE_SET_FILES
    ]


def _valid_rule_set_file(path: Path) -> bool:
    """Return whether ``path`` looks like a downloaded binary rule set."""
    if not path.is_file() or path.stat().st_size == 0:
        return False
    # A proxy/CDN error page must not be mistaken for an srs file.  Do this
    # small check without imposing a format parser on sing-box's own binary.
    try:
        with path.open("rb") as stream:
            prefix = stream.read(256).lstrip().lower()
    except OSError:
        return False
    return not prefix.startswith((b"<html", b"<!doctype", b"{\"error"))


def all_rule_sets_present(directory: Path | str) -> bool:
    """Check that every manifest asset is present and non-empty."""
    rule_dir = Path(directory).expanduser().resolve()
    return all(_valid_rule_set_file(rule_dir / filename) for filename in RULE_SET_FILES)


def _download_rule_set(url: str, destination: Path) -> None:
    """Download one rule set to an already-created temporary destination."""
    result = subprocess.run(
        [
            "curl",
            "-sSL",
            "-f",
            "--connect-timeout",
            "20",
            "--max-time",
            "300",
            "-o",
            str(destination),
            url,
        ],
        capture_output=True,
        text=True,
        timeout=330,
        env=clean_subprocess_env(),
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "curl failed").strip()
        raise RuntimeError(f"failed to download {url}: {detail}")
    if not _valid_rule_set_file(destination):
        raise RuntimeError(f"downloaded invalid rule set from {url}")


def ensure_rule_sets(directory: Path | str) -> Dict[str, Any]:
    """Ensure all rule sets exist, replacing each file only after validation.

    Existing valid files are reused.  Each missing file is downloaded into a
    sibling temporary file and atomically renamed, so a failed refresh cannot
    destroy an already usable asset.
    """
    rule_dir = Path(directory).expanduser().resolve()
    rule_dir.mkdir(parents=True, exist_ok=True)
    missing = [
        filename
        for filename in RULE_SET_FILES
        if not _valid_rule_set_file(rule_dir / filename)
    ]
    if not missing:
        return {"success": True, "path": str(rule_dir), "missing": []}

    try:
        for filename in missing:
            destination = rule_dir / filename
            temp_name = f".{filename}.{uuid.uuid4().hex}.tmp"
            temporary = rule_dir / temp_name
            try:
                _download_rule_set(RULE_SET_SOURCES[filename], temporary)
                os.replace(temporary, destination)
            finally:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass
    except Exception as exc:
        remaining = [
            filename
            for filename in RULE_SET_FILES
            if not _valid_rule_set_file(rule_dir / filename)
        ]
        return {
            "success": False,
            "path": str(rule_dir),
            "missing": remaining,
            "errorCode": "RULESET_DOWNLOAD_FAILED",
            "error": str(exc),
        }

    return {"success": True, "path": str(rule_dir), "missing": []}
