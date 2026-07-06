"""Tests for backend.src.update_checker (no network access)."""

import asyncio

from backend.src import update_checker


def test_parse_version():
    assert update_checker.parse_version("v1.2.3") == (1, 2, 3)
    assert update_checker.parse_version("1.11.15") == (1, 11, 15)
    assert update_checker.parse_version("v26.3.27") == (26, 3, 27)
    assert update_checker.parse_version("v1.2.3-beta.1") == (1, 2, 3)
    assert update_checker.parse_version("nightly") == ()
    assert update_checker.parse_version(None) == ()


def test_compare_versions():
    assert update_checker.compare_versions("v1.2.3", "v1.2.3") == 0
    assert update_checker.compare_versions("v1.2.3", "v1.2.4") == -1
    assert update_checker.compare_versions("v1.3.0", "v1.2.9") == 1
    # Differing lengths pad with zeros: 1.2 == 1.2.0.
    assert update_checker.compare_versions("v1.2", "v1.2.0") == 0
    assert update_checker.compare_versions("v1.2.1", "v1.2") == 1
    # Numeric, not lexical: 10 > 9.
    assert update_checker.compare_versions("v1.10.0", "v1.9.0") == 1


def test_check_core_updates_flags_newer(monkeypatch):
    latest = {
        "XTLS/Xray-core": "v99.0.0",
        "SagerNet/sing-box": "v1.11.15",
    }

    async def fake_fetch(_session, repo):
        return latest.get(repo)

    monkeypatch.setattr(update_checker, "_fetch_latest_tag", fake_fetch)
    result = asyncio.run(update_checker.check_core_updates(session=object()))
    by_name = {c["name"]: c for c in result}

    assert by_name["xray-core"]["updateAvailable"] is True
    assert by_name["xray-core"]["latest"] == "v99.0.0"
    # sing-box latest equals the pin → no update.
    assert by_name["sing-box"]["updateAvailable"] is False


def test_check_core_updates_handles_fetch_failure(monkeypatch):
    async def fake_fetch(_session, _repo):
        return None

    monkeypatch.setattr(update_checker, "_fetch_latest_tag", fake_fetch)
    result = asyncio.run(update_checker.check_core_updates(session=object()))

    assert len(result) == 2
    for core in result:
        assert core["latest"] is None
        assert core["updateAvailable"] is False
        assert core["current"]  # the pinned version is always reported


def test_plugin_version_reads_package_json():
    # The bundled package.json is present in the repo; a real version string.
    version = update_checker.plugin_version()
    assert isinstance(version, str) and version


def test_check_updates_includes_plugin(monkeypatch):
    latest = {update_checker.PLUGIN_REPO: "v99.0.0"}

    async def fake_fetch(_session, repo):
        return latest.get(repo)

    monkeypatch.setattr(update_checker, "_fetch_latest_tag", fake_fetch)
    monkeypatch.setattr(update_checker, "plugin_version", lambda: "1.0.1")
    result = asyncio.run(update_checker.check_updates(session=object()))

    assert result[0]["kind"] == "plugin"
    assert result[0]["name"] == "xray-decky"
    assert result[0]["updateAvailable"] is True  # v99 > 1.0.1
    # Cores still follow the plugin entry.
    assert {c["kind"] for c in result[1:]} == {"core"}


def test_check_updates_skips_plugin_when_version_unknown(monkeypatch):
    async def fake_fetch(_session, _repo):
        return None

    monkeypatch.setattr(update_checker, "_fetch_latest_tag", fake_fetch)
    monkeypatch.setattr(update_checker, "plugin_version", lambda: None)
    result = asyncio.run(update_checker.check_updates(session=object()))

    assert all(c["kind"] == "core" for c in result)
