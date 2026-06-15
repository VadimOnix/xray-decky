"""Tests for backend.src.xray_downloader (no network access)."""

import io
import os
import zipfile
from pathlib import Path

from backend.src import xray_downloader


def _make_release_zip(path: Path, *, with_geo: bool = True) -> None:
    """Create a fake Xray-linux-64.zip with the expected member layout."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(xray_downloader.ARCHIVE_BINARY_NAME, b"#!/bin/sh\necho xray\n")
        if with_geo:
            zf.writestr("geoip.dat", b"geoip-data")
            zf.writestr("geosite.dat", b"geosite-data")
    path.write_bytes(buf.getvalue())


def test_binary_present(tmp_path: Path) -> None:
    binary = tmp_path / "xray-core"
    assert not xray_downloader.binary_present(binary)

    binary.write_text("binary")
    # Exists but not executable.
    os.chmod(binary, 0o644)
    assert not xray_downloader.binary_present(binary)

    os.chmod(binary, 0o755)
    assert xray_downloader.binary_present(binary)


def test_geo_files_present(tmp_path: Path) -> None:
    assert not xray_downloader.geo_files_present(tmp_path)
    (tmp_path / "geoip.dat").write_text("a")
    assert not xray_downloader.geo_files_present(tmp_path)
    (tmp_path / "geosite.dat").write_text("b")
    assert xray_downloader.geo_files_present(tmp_path)


def test_ensure_skips_download_when_present(tmp_path: Path, monkeypatch) -> None:
    binary = tmp_path / "xray-core"
    binary.write_text("binary")
    os.chmod(binary, 0o755)
    (tmp_path / "geoip.dat").write_text("a")
    (tmp_path / "geosite.dat").write_text("b")

    def _fail_download(*_args, **_kwargs):
        raise AssertionError("download should not be called when files are present")

    monkeypatch.setattr(xray_downloader, "download_xray", _fail_download)

    result = xray_downloader.ensure_xray_binary(binary)
    assert result["success"] is True
    assert result["alreadyPresent"] is True
    assert result["path"] == str(binary)


def test_download_extracts_binary_and_geo(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "bin"

    def _fake_download_file(url: str, dest: Path) -> bool:
        assert "v9.9.9" in url and xray_downloader.XRAY_ASSET in url
        _make_release_zip(Path(dest), with_geo=True)
        return True

    monkeypatch.setattr(xray_downloader, "_download_file", _fake_download_file)

    result = xray_downloader.download_xray(target, version="v9.9.9")
    assert result["success"] is True, result
    assert result["version"] == "v9.9.9"

    binary = target / xray_downloader.BINARY_NAME
    assert binary.is_file()
    assert os.access(binary, os.X_OK)
    assert (target / "geoip.dat").is_file()
    assert (target / "geosite.dat").is_file()


def test_download_uses_latest_when_version_unset(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(xray_downloader, "fetch_latest_version", lambda: "v1.2.3")

    captured = {}

    def _fake_download_file(url: str, dest: Path) -> bool:
        captured["url"] = url
        _make_release_zip(Path(dest))
        return True

    monkeypatch.setattr(xray_downloader, "_download_file", _fake_download_file)

    result = xray_downloader.download_xray(tmp_path / "bin")
    assert result["success"] is True
    assert result["version"] == "v1.2.3"
    assert "v1.2.3" in captured["url"]


def test_download_falls_back_when_api_down(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(xray_downloader, "fetch_latest_version", lambda: None)
    monkeypatch.setattr(
        xray_downloader, "_download_file", lambda url, dest: _make_release_zip(Path(dest)) or True
    )

    result = xray_downloader.download_xray(tmp_path / "bin")
    assert result["success"] is True
    assert result["version"] == xray_downloader.FALLBACK_XRAY_VERSION


def test_download_reports_download_failure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(xray_downloader, "_download_file", lambda url, dest: False)
    result = xray_downloader.download_xray(tmp_path / "bin", version="v9.9.9")
    assert result["success"] is False
    assert result["errorCode"] == "DOWNLOAD_FAILED"


def test_download_reports_invalid_archive(tmp_path: Path, monkeypatch) -> None:
    def _bad_zip(url: str, dest: Path) -> bool:
        Path(dest).write_bytes(b"not a zip file")
        return True

    monkeypatch.setattr(xray_downloader, "_download_file", _bad_zip)
    result = xray_downloader.download_xray(tmp_path / "bin", version="v9.9.9")
    assert result["success"] is False
    assert result["errorCode"] == "ARCHIVE_INVALID"
