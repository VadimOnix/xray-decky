#!/bin/bash
# xray-decky network recovery script.
#
# Restores connectivity if the plugin ever dies without cleaning up
# (kill switch chain left in the firewall, stale TUN route, system proxy
# still pointing at a dead xray-core). Safe to run repeatedly; every step
# is best-effort and idempotent.
#
# Usage (Desktop Mode terminal on the Steam Deck):
#   sudo bash recover.sh

set -u

CHAIN="XRAY_KILLSWITCH"
TUN_IF="xray0"

if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root: sudo bash $0" >&2
  exit 1
fi

echo "== xray-decky network recovery =="

# 1. Remove the kill switch chain (IPv4 + IPv6). Unhook every reference
#    from OUTPUT first, then flush and delete the chain itself.
for fw in iptables ip6tables; do
  if command -v "$fw" >/dev/null 2>&1; then
    while "$fw" -w 5 -C OUTPUT -j "$CHAIN" 2>/dev/null; do
      "$fw" -w 5 -D OUTPUT -j "$CHAIN" 2>/dev/null || break
    done
    "$fw" -w 5 -F "$CHAIN" 2>/dev/null || true
    "$fw" -w 5 -X "$CHAIN" 2>/dev/null || true
    echo "  [$fw] kill switch chain removed (if it existed)"
  fi
done

# 2. Remove TUN routing (current default-route scheme + legacy fwmark rules).
ip route del default dev "$TUN_IF" 2>/dev/null || true
ip rule del fwmark 0x206 table 100 2>/dev/null || true
ip route del default table 100 2>/dev/null || true
ip link del "$TUN_IF" 2>/dev/null || true
echo "  routes and $TUN_IF cleaned up"

# 3. Stop any leftover xray-core processes started by the plugin.
pkill -x xray-core 2>/dev/null || true
echo "  xray-core processes stopped"

# 4. Turn the desktop session's system proxy off (GNOME/GTK + KDE/Qt).
#    Run as the desktop user when invoked via sudo.
TARGET_USER="${SUDO_USER:-deck}"
if command -v gsettings >/dev/null 2>&1; then
  sudo -u "$TARGET_USER" gsettings set org.gnome.system.proxy mode none 2>/dev/null || true
fi
if command -v kwriteconfig5 >/dev/null 2>&1; then
  sudo -u "$TARGET_USER" kwriteconfig5 --file kioslaverc \
    --group "Proxy Settings" --key ProxyType 0 2>/dev/null || true
fi
echo "  system proxy disabled"

echo "Done. If connectivity is still broken, reboot the Deck."
