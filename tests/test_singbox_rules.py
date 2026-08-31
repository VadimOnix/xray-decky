"""Tests for the shared sing-box .srs rule-set manifest and downloader."""

from pathlib import Path

import pytest

from backend.src import singbox_rules


EXPECTED_FILES = (
    "geoip-cn.srs",
    "geoip-facebook.srs",
    "geoip-fastly.srs",
    "geoip-google.srs",
    "geoip-netflix.srs",
    "geoip-private.srs",
    "geoip-telegram.srs",
    "geoip-twitter.srs",
    "geosite-category-ads-all.srs",
    "geosite-category-games@cn.srs",
    "geosite-cn.srs",
    "geosite-geolocation-!cn.srs",
    "geosite-geolocation-cn.srs",
    "geosite-gfw.srs",
    "geosite-google.srs",
    "geosite-greatfire.srs",
    "geosite-private.srs",
    "geosite-steam@cn.srs",
    "geosite-xbox@cn.srs",
)


def test_manifest_matches_requested_v2rayn_rule_sets():
    assert singbox_rules.RULE_SET_FILES == EXPECTED_FILES
    assert len(singbox_rules.RULE_SET_SOURCES) == len(EXPECTED_FILES)
    for filename in EXPECTED_FILES[:8]:
        assert "/rule-set-geoip/" in singbox_rules.RULE_SET_SOURCES[filename]
    for filename in EXPECTED_FILES[8:]:
        assert "/rule-set-geosite/" in singbox_rules.RULE_SET_SOURCES[filename]


@pytest.mark.parametrize(
    ("value", "tag"),
    [
        ("geosite:cn", "geosite-cn"),
        ("geosite:category-games@cn", "geosite-category-games@cn"),
        ("geosite:geolocation-cn", "geosite-geolocation-cn"),
        ("geoip:private", "geoip-private"),
    ],
)
def test_rule_set_tag_strips_only_the_core_prefix(value, tag):
    assert singbox_rules.rule_set_tag(value) == tag


def test_rule_set_definitions_are_local_binary_files(tmp_path):
    definitions = singbox_rules.rule_set_definitions(tmp_path)
    assert [item["tag"] for item in definitions] == [
        Path(name).stem for name in EXPECTED_FILES
    ]
    assert all(item["type"] == "local" for item in definitions)
    assert all(item["format"] == "binary" for item in definitions)
    assert all(Path(item["path"]).parent == tmp_path for item in definitions)


def test_ensure_rule_sets_downloads_missing_files_atomically(monkeypatch, tmp_path):
    downloaded = []

    def fake_download(url, destination):
        downloaded.append((url, destination.name))
        destination.write_bytes(b"valid-srs")

    monkeypatch.setattr(singbox_rules, "_download_rule_set", fake_download)
    result = singbox_rules.ensure_rule_sets(tmp_path)

    assert result["success"] is True
    assert result["path"] == str(tmp_path)
    assert len(downloaded) == len(EXPECTED_FILES)
    assert all(
        (tmp_path / filename).read_bytes() == b"valid-srs"
        for filename in EXPECTED_FILES
    )


def test_ensure_rule_sets_keeps_existing_files_when_a_download_fails(
    monkeypatch, tmp_path
):
    existing = tmp_path / EXPECTED_FILES[0]
    existing.write_bytes(b"existing")

    def fake_download(url, destination):
        if url.endswith("/" + EXPECTED_FILES[1]):
            raise RuntimeError("offline")
        destination.write_bytes(b"new")

    monkeypatch.setattr(singbox_rules, "_download_rule_set", fake_download)
    result = singbox_rules.ensure_rule_sets(tmp_path)

    assert result["success"] is False
    assert result["errorCode"] == "RULESET_DOWNLOAD_FAILED"
    assert existing.read_bytes() == b"existing"
