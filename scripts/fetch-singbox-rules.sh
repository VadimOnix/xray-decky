#!/usr/bin/env bash
# Fetch the binary sing-box rule sets used by the route-rule feature.
set -euo pipefail

TARGET_DIR="${1:?usage: $0 <target-dir>}"
mkdir -p "$TARGET_DIR"

BASE_URL="https://raw.githubusercontent.com/2dust/sing-box-rules"
GEOIP_FILES=(
  geoip-cn.srs
  geoip-facebook.srs
  geoip-fastly.srs
  geoip-google.srs
  geoip-netflix.srs
  geoip-private.srs
  geoip-telegram.srs
  geoip-twitter.srs
)
GEOSITE_FILES=(
  geosite-category-ads-all.srs
  geosite-category-games@cn.srs
  geosite-cn.srs
  geosite-geolocation-!cn.srs
  geosite-geolocation-cn.srs
  geosite-gfw.srs
  geosite-google.srs
  geosite-greatfire.srs
  geosite-private.srs
  geosite-steam@cn.srs
  geosite-xbox@cn.srs
)

fetch_one() {
  local branch="$1"
  local filename="$2"
  local destination="$TARGET_DIR/$filename"
  local temporary

  if valid_rule_set "$destination"; then
    return
  fi

  temporary="$(mktemp "$TARGET_DIR/.${filename}.XXXXXX.tmp")"
  if ! curl -sSL -f --connect-timeout 20 --max-time 300 \
      -o "$temporary" "$BASE_URL/$branch/$filename"; then
    rm -f -- "$temporary"
    echo "Failed to download $filename" >&2
    exit 1
  fi
  if ! valid_rule_set "$temporary"; then
    rm -f -- "$temporary"
    echo "Downloaded invalid rule set: $filename" >&2
    exit 1
  fi
  mv -f -- "$temporary" "$destination"
}

valid_rule_set() {
  local path="$1"
  [[ -s "$path" ]] || return 1
  if head -c 256 "$path" | grep -Eiq '^[[:space:]]*(<html|<!doctype|\{"error)'; then
    return 1
  fi
  return 0
}

for filename in "${GEOIP_FILES[@]}"; do
  fetch_one rule-set-geoip "$filename"
done
for filename in "${GEOSITE_FILES[@]}"; do
  fetch_one rule-set-geosite "$filename"
done
