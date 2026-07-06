"""Tests for backend.src.singbox_downloader (no network access)."""

import io
import os
import tarfile
from pathlib import Path

from backend.src import singbox_downloader


def _make_release_tar(path: Path, *, binary_name: str = "sing-box") -> None:
    """Create a fake sing-box-<v>-linux-amd64.tar.gz with the member layout."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        data = b"#!/bin/sh\necho sing-box\n"
        info = tarfile.TarInfo(name=f"sing-box-1.11.15-linux-amd64/{binary_name}")
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    path.write_bytes(buf.getvalue())


def test_binary_present(tmp_path: Path) -> None:
    binary = tmp_path / "sing-box"
    assert not singbox_downloader.binary_present(binary)
    binary.write_text("binary")
    os.chmod(binary, 0o644)
    assert not singbox_downloader.binary_present(binary)
    os.chmod(binary, 0o755)
    assert singbox_downloader.binary_present(binary)


def test_resolve_asset_strips_v():
    resolved = singbox_downloader._resolve_asset(
        "sing-box-{version_no_v}-linux-amd64.tar.gz", "v1.11.15"
    )
    assert resolved == "sing-box-1.11.15-linux-amd64.tar.gz"


def test_load_pin_non_object(monkeypatch, tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text('"just a string"')
    monkeypatch.setattr(singbox_downloader, "_VERSION_FILE", bad)
    assert singbox_downloader._load_pin() == {}
    assert singbox_downloader.pinned_version() == (
        singbox_downloader.FALLBACK_SINGBOX_VERSION
    )


def test_download_extracts_binary(monkeypatch, tmp_path: Path):
    target = tmp_path / "install"

    def fake_download(url, dest):
        _make_release_tar(Path(dest))
        return True

    monkeypatch.setattr(singbox_downloader, "_download_file", fake_download)
    monkeypatch.setattr(
        singbox_downloader,
        "_load_pin",
        lambda: {
            "repo": "SagerNet/sing-box",
            "asset": "sing-box-{version_no_v}-linux-amd64.tar.gz",
            "version": "v1.11.15",
        },
    )

    result = singbox_downloader.download_singbox(target)
    assert result["success"] is True
    assert result["version"] == "v1.11.15"
    binary = target / "sing-box"
    assert singbox_downloader.binary_present(binary)


def test_download_checksum_mismatch(monkeypatch, tmp_path: Path):
    target = tmp_path / "install"

    def fake_download(url, dest):
        _make_release_tar(Path(dest))
        return True

    monkeypatch.setattr(singbox_downloader, "_download_file", fake_download)
    monkeypatch.setattr(
        singbox_downloader,
        "_load_pin",
        lambda: {
            "asset": "sing-box-{version_no_v}-linux-amd64.tar.gz",
            "version": "v1.11.15",
            "sha256": "00" * 32,
        },
    )

    result = singbox_downloader.download_singbox(target)
    assert result["success"] is False
    assert result["errorCode"] == "CHECKSUM_MISMATCH"


def test_download_bad_archive(monkeypatch, tmp_path: Path):
    target = tmp_path / "install"

    def fake_download(url, dest):
        Path(dest).write_bytes(b"not a tarball")
        return True

    monkeypatch.setattr(singbox_downloader, "_download_file", fake_download)
    monkeypatch.setattr(
        singbox_downloader,
        "_load_pin",
        lambda: {
            "asset": "sing-box-{version_no_v}-linux-amd64.tar.gz",
            "version": "v1.11.15",
        },
    )

    result = singbox_downloader.download_singbox(target)
    assert result["success"] is False
    assert result["errorCode"] == "ARCHIVE_INVALID"


def test_ensure_skips_when_present(monkeypatch, tmp_path: Path):
    binary = tmp_path / "sing-box"
    binary.write_text("x")
    os.chmod(binary, 0o755)

    def fail_download(*_args, **_kwargs):
        raise AssertionError("should not download when present")

    monkeypatch.setattr(singbox_downloader, "download_singbox", fail_download)
    result = singbox_downloader.ensure_singbox_binary(binary)
    assert result["alreadyPresent"] is True
