"""
Telemetry-free update checker for the bundled cores.

Compares the pinned xray-core / sing-box versions (backend/src/*_version.json)
against the latest GitHub release tag for each core's repo. Nothing about the
install or the user is sent — it is an anonymous GET to the public GitHub
releases API, made only when explicitly requested from the admin panel.
"""

import json
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from backend.src import singbox_downloader, xray_downloader

_RELEASE_API = "https://api.github.com/repos/{repo}/releases/latest"
_REQUEST_TIMEOUT = 10
# GitHub's release JSON is a few KiB; cap defensively so a hostile/redirected
# endpoint can't stream an unbounded body into memory.
_MAX_BODY_BYTES = 1 * 1024 * 1024


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


def _core_entry(
    name: str, repo: str, current: str, latest: Optional[str]
) -> Dict[str, Any]:
    return {
        "name": name,
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
            results.append(_core_entry(name, repo, current, latest))
        return results
    finally:
        if owns_session:
            await session.close()
