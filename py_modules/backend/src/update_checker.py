"""
Telemetry-free update checker for the plugin and the bundled cores.

Compares the plugin's own version (package.json) and the pinned xray-core /
sing-box versions (py_modules/backend/src/*_version.json) against the latest GitHub
release tag for each repo. Nothing about the install or the user is sent — it
is an anonymous GET to the public GitHub releases API, made only when
explicitly requested from the admin panel.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from backend.src import singbox_downloader, xray_downloader

_RELEASE_API = "https://api.github.com/repos/{repo}/releases/latest"
_REQUEST_TIMEOUT = 10
# GitHub's release JSON is a few KiB; cap defensively so a hostile/redirected
# endpoint can't stream an unbounded body into memory.
_MAX_BODY_BYTES = 1 * 1024 * 1024

# The plugin's own GitHub repository (releases are published here).
PLUGIN_REPO = "VadimOnix/xray-decky"
# py_modules/backend/src -> plugin root
_PACKAGE_JSON = Path(__file__).resolve().parents[3] / "package.json"


def plugin_version() -> Optional[str]:
    """The plugin's current version from package.json, or None if unreadable."""
    try:
        with open(_PACKAGE_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    version = data.get("version") if isinstance(data, dict) else None
    return str(version) if version else None


def parse_version(tag: Any) -> Tuple[int, ...]:
    """Turn a ``vX.Y.Z`` tag into a comparable int tuple.

    Leading ``v`` is dropped; each dotted chunk contributes its leading digits
    (so ``v1.2.3-beta`` → ``(1, 2, 3)``). Returns ``()`` for anything that does
    not begin with a numeric component, which sorts below every real version.
    """
    if not isinstance(tag, str):
        return ()
    text = tag.strip()
    if text[:1] in ("v", "V"):
        text = text[1:]
    parts: List[int] = []
    for chunk in text.split("."):
        if chunk.isdigit():
            parts.append(int(chunk))
            continue
        # First chunk with a non-digit suffix (e.g. "3-beta") ends the version:
        # take its leading digits, then stop — the rest is a pre-release tail.
        digits = ""
        for ch in chunk:
            if ch.isdigit():
                digits += ch
            else:
                break
        if digits:
            parts.append(int(digits))
        break
    return tuple(parts)


def compare_versions(a: Any, b: Any) -> int:
    """Return -1/0/1 comparing version tags ``a`` and ``b`` numerically."""
    pa, pb = parse_version(a), parse_version(b)
    width = max(len(pa), len(pb))
    pa = pa + (0,) * (width - len(pa))
    pb = pb + (0,) * (width - len(pb))
    if pa < pb:
        return -1
    if pa > pb:
        return 1
    return 0


async def _fetch_latest_tag(
    session: aiohttp.ClientSession, repo: str
) -> Optional[str]:
    """Return the latest release tag for ``repo``, or None on any failure."""
    url = _RELEASE_API.format(repo=repo)
    try:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=_REQUEST_TIMEOUT),
            headers={"Accept": "application/vnd.github+json"},
        ) as resp:
            if resp.status != 200:
                return None
            raw = await resp.content.read(_MAX_BODY_BYTES + 1)
            if len(raw) > _MAX_BODY_BYTES:
                return None
            data = json.loads(raw.decode("utf-8", "replace"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    tag = data.get("tag_name")
    return tag if isinstance(tag, str) and tag else None


def _entry(
    name: str, kind: str, repo: str, current: str, latest: Optional[str]
) -> Dict[str, Any]:
    return {
        "name": name,
        "kind": kind,
        "repo": repo,
        "current": current,
        "latest": latest,
        "updateAvailable": bool(latest) and compare_versions(latest, current) > 0,
    }


async def check_core_updates(
    session: Optional[aiohttp.ClientSession] = None,
) -> List[Dict[str, Any]]:
    """Check the bundled cores against their latest GitHub releases.

    Returns one entry per core with its pinned ``current`` version, the fetched
    ``latest`` tag (None when the check failed) and an ``updateAvailable`` flag.
    """
    cores = [
        (
            "xray-core",
            xray_downloader.pinned_repo(),
            xray_downloader.pinned_version(),
        ),
        (
            "sing-box",
            singbox_downloader.pinned_repo(),
            singbox_downloader.pinned_version(),
        ),
    ]

    owns_session = session is None
    if owns_session:
        session = aiohttp.ClientSession()
    try:
        results = []
        for name, repo, current in cores:
            latest = await _fetch_latest_tag(session, repo)
            results.append(_entry(name, "core", repo, current, latest))
        return results
    finally:
        if owns_session:
            await session.close()


async def check_updates(
    session: Optional[aiohttp.ClientSession] = None,
) -> List[Dict[str, Any]]:
    """Check the plugin and the bundled cores against their latest releases.

    The plugin entry comes first (when its version is readable), followed by
    the core entries from :func:`check_core_updates`.
    """
    owns_session = session is None
    if owns_session:
        session = aiohttp.ClientSession()
    try:
        results: List[Dict[str, Any]] = []
        current = plugin_version()
        if current:
            latest = await _fetch_latest_tag(session, PLUGIN_REPO)
            results.append(
                _entry("xray-decky", "plugin", PLUGIN_REPO, current, latest)
            )
        results.extend(await check_core_updates(session=session))
        return results
    finally:
        if owns_session:
            await session.close()
