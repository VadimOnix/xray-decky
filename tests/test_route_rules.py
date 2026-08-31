"""Tests for backend.src.route_rules (user-editable routing rules)."""

import copy

import pytest

from backend.src.route_rules import (
    MAX_RULES,
    ROUTE_RULES_KEY,
    SCHEMA_VERSION,
    RouteRulesStore,
    validate_rule,
)
from backend.src.singbox_rules import RULE_SET_FILES, rule_set_tag


class _FakeSettings:
    def __init__(self, initial=None):
        self.data = dict(initial or {})
        self.commits = 0

    def getSetting(self, key, default=None):
        return self.data.get(key, default)

    def setSetting(self, key, value):
        self.data[key] = value

    def commit(self):
        self.commits += 1


# ----- validation -----


def test_validate_rule_domain_basic():
    rule = {
        "id": "a1",
        "enabled": True,
        "action": "proxy",
        "match": {"type": "domain", "value": "example.com"},
    }
    validate_rule(rule)  # should not raise


def test_validate_rule_domain_with_explicit_prefix():
    rule = {
        "id": "a1",
        "enabled": True,
        "action": "proxy",
        "match": {"type": "domain", "value": "domain:example.com"},
    }
    validate_rule(rule)


def test_validate_rule_domain_strips_keyword_prefix():
    rule = {
        "id": "a1",
        "enabled": True,
        "action": "direct",
        "match": {"type": "domain", "value": "keyword:tracker"},
    }
    validate_rule(rule)


def test_validate_rule_ip_cidr():
    rule = {
        "id": "a1",
        "enabled": True,
        "action": "reject",
        "match": {"type": "ip", "value": "10.0.0.0/8"},
    }
    validate_rule(rule)


def test_validate_rule_ip_single_address():
    rule = {
        "id": "a1",
        "enabled": True,
        "action": "direct",
        "match": {"type": "ip", "value": "192.168.1.1"},
    }
    validate_rule(rule)


def test_validate_rule_geosite_and_geoip_require_prefix():
    rule_ok = {
        "id": "a1",
        "enabled": True,
        "action": "proxy",
        "match": {"type": "geosite", "value": "geosite:google"},
    }
    validate_rule(rule_ok)
    rule_bad = {
        "id": "a1",
        "enabled": True,
        "action": "proxy",
        "match": {"type": "geosite", "value": "google"},
    }
    with pytest.raises(ValueError):
        validate_rule(rule_bad)


@pytest.mark.parametrize(
    "value",
    [
        "geosite:category-games@cn",
        "geosite:steam@cn",
        "geosite:xbox@cn",
        "geosite:geolocation-!cn",
        "geoip:private",
    ],
)
def test_validate_rule_accepts_real_v2rayn_categories(value):
    kind = "geoip" if value.startswith("geoip:") else "geosite"
    validate_rule(
        {
            "id": "a1",
            "enabled": True,
            "action": "direct",
            "match": {"type": kind, "value": value},
        }
    )


def test_validate_rule_rejects_unknown_type():
    rule = {
        "id": "a1",
        "enabled": True,
        "action": "proxy",
        "match": {"type": "process", "value": "steam"},
    }
    with pytest.raises(ValueError):
        validate_rule(rule)


def test_validate_rule_rejects_unknown_action():
    rule = {
        "id": "a1",
        "enabled": True,
        "action": "drop",
        "match": {"type": "domain", "value": "x.com"},
    }
    with pytest.raises(ValueError):
        validate_rule(rule)


def test_validate_rule_rejects_bad_cidr():
    rule = {
        "id": "a1",
        "enabled": True,
        "action": "proxy",
        "match": {"type": "ip", "value": "10.0.0.999/8"},
    }
    with pytest.raises(ValueError):
        validate_rule(rule)


def test_validate_rule_requires_id_enabled_action_match():
    with pytest.raises(ValueError):
        validate_rule(
            {"enabled": True, "action": "proxy", "match": {"type": "domain", "value": "x"}}
        )
    with pytest.raises(ValueError):
        validate_rule(
            {
                "id": "a",
                "action": "proxy",
                "match": {"type": "domain", "value": "x"},
            }
        )
    with pytest.raises(ValueError):
        validate_rule(
            {
                "id": "a",
                "enabled": True,
                "match": {"type": "domain", "value": "x"},
            }
        )


# ----- store CRUD -----


def test_empty_store_returns_empty_list():
    store = RouteRulesStore(_FakeSettings())
    assert store.list_rules() == []


def test_add_assigns_id_and_persists():
    settings = _FakeSettings()
    store = RouteRulesStore(settings)
    rule_id = store.add_rule(
        {
            "enabled": True,
            "action": "proxy",
            "match": {"type": "domain", "value": "example.com"},
        }
    )
    assert isinstance(rule_id, str) and len(rule_id) > 0
    rules = store.list_rules()
    assert len(rules) == 1
    assert rules[0]["id"] == rule_id
    assert rules[0]["enabled"] is True
    assert settings.data[ROUTE_RULES_KEY]["version"] == SCHEMA_VERSION
    assert settings.commits >= 1


def test_add_rejects_invalid_rule():
    store = RouteRulesStore(_FakeSettings())
    with pytest.raises(ValueError):
        store.add_rule({"match": {"type": "ip", "value": "10.0.0.999/8"}})


def test_update_rule_partial():
    settings = _FakeSettings()
    store = RouteRulesStore(settings)
    rule_id = store.add_rule(
        {
            "enabled": True,
            "action": "proxy",
            "match": {"type": "domain", "value": "example.com"},
        }
    )
    assert store.update_rule(rule_id, {"action": "direct", "enabled": False})
    rule = store.get_rule(rule_id)
    assert rule["action"] == "direct"
    assert rule["enabled"] is False
    assert rule["match"]["value"] == "example.com"


def test_update_rule_unknown_id_returns_false():
    store = RouteRulesStore(_FakeSettings())
    assert store.update_rule("nope", {"enabled": False}) is False


def test_delete_rule():
    settings = _FakeSettings()
    store = RouteRulesStore(settings)
    rule_id = store.add_rule(
        {
            "enabled": True,
            "action": "proxy",
            "match": {"type": "domain", "value": "x.com"},
        }
    )
    assert store.delete_rule(rule_id) is True
    assert store.list_rules() == []
    assert store.delete_rule(rule_id) is False  # already gone


def test_reorder_preserves_only_specified_ids():
    settings = _FakeSettings()
    store = RouteRulesStore(settings)
    ids = [
        store.add_rule(
            {
                "enabled": True,
                "action": "proxy",
                "match": {"type": "domain", "value": f"{i}.com"},
            }
        )
        for i in range(3)
    ]
    # Reverse order
    assert store.reorder([ids[2], ids[0], ids[1]]) is True
    ordered = store.list_rules()
    assert [r["id"] for r in ordered] == [ids[2], ids[0], ids[1]]


def test_reorder_rejects_mismatch():
    settings = _FakeSettings()
    store = RouteRulesStore(settings)
    rid = store.add_rule(
        {
            "enabled": True,
            "action": "proxy",
            "match": {"type": "domain", "value": "x.com"},
        }
    )
    assert store.reorder(["something-else"]) is False
    assert [r["id"] for r in store.list_rules()] == [rid]


def test_set_rules_replaces_whole_list():
    settings = _FakeSettings()
    store = RouteRulesStore(settings)
    store.add_rule(
        {
            "enabled": True,
            "action": "proxy",
            "match": {"type": "domain", "value": "old.com"},
        }
    )
    new_rules = [
        {
            "id": "id1",
            "enabled": True,
            "action": "direct",
            "match": {"type": "geosite", "value": "geosite:cn"},
        },
        {
            "id": "id2",
            "enabled": True,
            "action": "reject",
            "match": {"type": "ip", "value": "1.2.3.0/24"},
        },
    ]
    store.set_rules(copy.deepcopy(new_rules))
    after = store.list_rules()
    assert [r["id"] for r in after] == ["id1", "id2"]
    assert after[1]["action"] == "reject"


def test_set_rules_rejects_invalid_rule():
    settings = _FakeSettings()
    store = RouteRulesStore(settings)
    with pytest.raises(ValueError):
        store.set_rules(
            [
                {
                    "id": "x",
                    "enabled": True,
                    "action": "proxy",
                    "match": {"type": "ip", "value": "bad"},
                }
            ]
        )


def test_max_rules_enforced():
    settings = _FakeSettings()
    store = RouteRulesStore(settings)
    for i in range(MAX_RULES):
        store.add_rule(
            {
                "enabled": True,
                "action": "proxy",
                "match": {"type": "domain", "value": f"{i}.com"},
            }
        )
    with pytest.raises(ValueError):
        store.add_rule(
            {
                "enabled": True,
                "action": "proxy",
                "match": {"type": "domain", "value": "overflow.com"},
            }
        )


# ----- presets -----


def test_presets_returns_curated_list():
    store = RouteRulesStore(_FakeSettings())
    presets = store.get_presets()
    assert isinstance(presets, list) and len(presets) >= 10
    # Every preset has the expected shape.
    for p in presets:
        assert set(p.keys()) >= {"type", "value"}
        assert p["type"] in {"geosite", "geoip"}
    # Has at least one of each common category.
    types = {p["type"] for p in presets}
    assert "geosite" in types
    assert "geoip" in types


def test_presets_match_v2rayn_categories():
    """Every category a user might expect from a v2rayN/Clash-style config
    should be present in the panel's typeahead. Locked here so trimming the
    list later is a conscious choice, not a regression.
    """
    presets = RouteRulesStore(_FakeSettings()).get_presets()
    values = {p["value"] for p in presets}
    expected = {
        # geoip
        "geoip:cn",
        "geoip:facebook",
        "geoip:fastly",
        "geoip:google",
        "geoip:netflix",
        "geoip:private",
        "geoip:telegram",
        "geoip:twitter",
        # geosite
        "geosite:cn",
        "geosite:google",
        "geosite:gfw",
        "geosite:greatfire",
        "geosite:private",
        "geosite:category-ads-all",
        "geosite:category-games@cn",
        "geosite:geolocation-cn",
        "geosite:steam@cn",
        "geosite:xbox@cn",
    }
    missing = expected - values
    assert not missing, f"preset list missing v2rayN-standard categories: {missing}"


def test_presets_are_backed_by_local_rule_sets():
    presets = RouteRulesStore(_FakeSettings()).get_presets()
    tags = {filename.removesuffix(".srs") for filename in RULE_SET_FILES}
    for index, preset in enumerate(presets):
        rule = {
            "id": f"preset-{index}",
            "enabled": True,
            "action": "direct",
            "match": preset,
        }
        validate_rule(rule)
        assert rule_set_tag(preset["value"]) in tags
