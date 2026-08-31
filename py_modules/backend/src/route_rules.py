"""
User-editable routing rules (domain / IP / geosite / geoip -> proxy|direct|reject).

Persisted under the "routeRules" settings key as
``{"version": 1, "rules": [...]}``. Single source of truth so both proxy cores
(xray-core and sing-box) emit the same user intent.

Validation rejects malformed values up front (bad CIDR, missing geosite: prefix,
unknown action, ...) so the config builders downstream can trust what they read.

The id field is opaque (UUID4-ish hex) — clients generate it on add, the server
re-generates on a set_rules() bulk replace. Reorder() enforces that the supplied
id list is a permutation of the stored set.
"""

import copy
import ipaddress
import re
import uuid
from typing import Any, Dict, List, Optional

from .singbox_rules import GEOIP_FILES, GEOSITE_FILES


ROUTE_RULES_KEY = "routeRules"
SCHEMA_VERSION = 1
MAX_RULES = 200

_MATCH_TYPES = ("domain", "ip", "geosite", "geoip")
_ACTIONS = ("proxy", "direct", "reject")
_DOMAIN_PREFIXES = ("domain:", "keyword:", "regexp:", "full:")
_GEO_PREFIXES = ("geosite:", "geoip:")
_CIDR_RE = re.compile(
    r"^(\d{1,3}\.){3}\d{1,3}$|"
    r"^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$"
)


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


def _validate_domain(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("domain value must be a non-empty string")
    stripped = value
    for prefix in _DOMAIN_PREFIXES:
        if stripped.startswith(prefix):
            stripped = stripped[len(prefix) :]
            break
    if not stripped:
        raise ValueError("domain value cannot be only a prefix")
    if "\n" in value or "\r" in value:
        raise ValueError("domain value must be single-line")


def _validate_ip(value: str) -> None:
    if not isinstance(value, str) or not _CIDR_RE.match(value):
        raise ValueError(f"ip value must be a CIDR or single address: {value!r}")
    try:
        ipaddress.ip_network(value, strict=False)
    except ValueError as exc:
        raise ValueError(f"invalid CIDR {value!r}: {exc}") from exc


def _validate_geosite_or_geoip(kind: str, value: str) -> None:
    prefix = f"{kind}:"
    if not isinstance(value, str) or not value.startswith(prefix):
        raise ValueError(f"{kind} value must start with '{prefix}': {value!r}")
    suffix = value[len(prefix) :]
    if not suffix or not re.match(r"^[a-zA-Z0-9_@!-]+$", suffix):
        raise ValueError(
            f"{kind} suffix contains unsupported characters: {suffix!r}"
        )


def validate_rule(rule: Dict[str, Any]) -> None:
    """Raise ValueError if `rule` does not match the schema. Mutates nothing."""
    if not isinstance(rule, dict):
        raise ValueError("rule must be an object")
    for key in ("id", "enabled", "action", "match"):
        if key not in rule:
            raise ValueError(f"rule missing required field: {key}")
    if not isinstance(rule["id"], str) or not rule["id"]:
        raise ValueError("rule.id must be a non-empty string")
    if not isinstance(rule["enabled"], bool):
        raise ValueError("rule.enabled must be boolean")
    if rule["action"] not in _ACTIONS:
        raise ValueError(
            f"rule.action must be one of {_ACTIONS}, got {rule['action']!r}"
        )
    match = rule["match"]
    if not isinstance(match, dict):
        raise ValueError("rule.match must be an object")
    m_type = match.get("type")
    if m_type not in _MATCH_TYPES:
        raise ValueError(
            f"rule.match.type must be one of {_MATCH_TYPES}, got {m_type!r}"
        )
    value = match.get("value", "")
    if m_type == "domain":
        _validate_domain(value)
    elif m_type == "ip":
        _validate_ip(value)
    elif m_type == "geosite":
        _validate_geosite_or_geoip("geosite", value)
    elif m_type == "geoip":
        _validate_geosite_or_geoip("geoip", value)


class RouteRulesStore:
    """CRUD over SettingsManager for the routeRules settings key."""

    def __init__(self, settings) -> None:
        self._settings = settings

    # ----- persistence -----

    def _load(self) -> Dict[str, Any]:
        data = self._settings.getSetting(ROUTE_RULES_KEY, None)
        if isinstance(data, dict) and isinstance(data.get("rules"), list):
            return data
        return {"version": SCHEMA_VERSION, "rules": []}

    def _save(self, data: Dict[str, Any]) -> None:
        data["version"] = SCHEMA_VERSION
        self._settings.setSetting(ROUTE_RULES_KEY, data)
        self._settings.commit()

    # ----- public CRUD -----

    def list_rules(self) -> List[Dict[str, Any]]:
        return [copy.deepcopy(r) for r in self._load()["rules"]]

    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        for r in self._load()["rules"]:
            if r.get("id") == rule_id:
                return copy.deepcopy(r)
        return None

    def add_rule(self, partial: Dict[str, Any]) -> str:
        """Append a rule; the server assigns it. Returns the new id."""
        data = self._load()
        if len(data["rules"]) >= MAX_RULES:
            raise ValueError(f"max {MAX_RULES} routing rules reached")
        rule = dict(partial)
        rule["id"] = _new_id()
        validate_rule(rule)
        data["rules"].append(rule)
        self._save(data)
        return rule["id"]

    def update_rule(self, rule_id: str, patch: Dict[str, Any]) -> bool:
        """Apply a partial update to a rule. Returns False if id not found."""
        data = self._load()
        for r in data["rules"]:
            if r.get("id") == rule_id:
                merged = dict(r)
                merged.update(patch)
                validate_rule(merged)
                data["rules"] = [
                    merged if item.get("id") == rule_id else item
                    for item in data["rules"]
                ]
                self._save(data)
                return True
        return False

    def delete_rule(self, rule_id: str) -> bool:
        data = self._load()
        before = len(data["rules"])
        data["rules"] = [r for r in data["rules"] if r.get("id") != rule_id]
        if len(data["rules"]) == before:
            return False
        self._save(data)
        return True

    def reorder(self, ids_in_order: List[str]) -> bool:
        """Set the order to exactly `ids_in_order`. Must be a permutation."""
        data = self._load()
        current = [r.get("id") for r in data["rules"]]
        if sorted(current) != sorted(ids_in_order) or len(current) != len(
            ids_in_order
        ):
            return False
        index = {rid: i for i, rid in enumerate(ids_in_order)}
        data["rules"].sort(key=lambda r: index.get(r.get("id"), 1 << 30))
        self._save(data)
        return True

    def set_rules(self, rules: List[Dict[str, Any]]) -> None:
        """Replace the whole list (used by the bulk PUT endpoint).

        Validates every rule up front and rejects the whole replace on any
        failure so the on-disk state never ends up half-applied.
        """
        if not isinstance(rules, list):
            raise ValueError("rules must be a list")
        if len(rules) > MAX_RULES:
            raise ValueError(f"max {MAX_RULES} routing rules")
        for r in rules:
            validate_rule(r)
        normalized = []
        seen_ids = set()
        for r in rules:
            normalized.append(dict(r))
            if r["id"] in seen_ids:
                raise ValueError(f"duplicate rule id: {r['id']}")
            seen_ids.add(r["id"])
        self._save({"version": SCHEMA_VERSION, "rules": normalized})

    # ----- presets -----

    def get_presets(self) -> List[Dict[str, str]]:
        """Curated list of geosite/geoip categories for the typeahead.

        Kept server-side so the same set is available to any client (the admin
        web panel today, a future mobile app tomorrow) and updates ship in one
        place. Order = display order in the typeahead.

        Derived from the local sing-box rule-set manifest so every advertised
        category has a corresponding asset at runtime. Xray maps these same
        values to its bundled geoip.dat/geosite.dat names.
        """
        def values(kind: str, filenames: tuple[str, ...]) -> List[Dict[str, str]]:
            prefix = f"{kind}-"
            return [
                {
                    "type": kind,
                    "value": f"{kind}:{filename[len(prefix):-4]}",
                }
                for filename in filenames
            ]

        return values("geosite", GEOSITE_FILES) + values("geoip", GEOIP_FILES)
