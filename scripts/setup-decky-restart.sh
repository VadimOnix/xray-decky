#!/bin/bash
# Run ON the Steam Deck to enable passwordless deploy automation.
#
# Installs /etc/sudoers.d/zzz-decky-restart with two NOPASSWD rules for the
# 'deck' user, so watch-mode deploys (DECK_RESTART=1) never prompt for a
# password on the device:
#   1. chown -R deck:deck <plugins-dir>/xray-decky
#      (plugin_loader runs as root; after a restart it can leave the plugin
#      dir root-owned, which would block the next rsync as user deck)
#   2. systemctl restart plugin_loader
#
# Usage (from your PC, per docs/DEVELOPMENT.md):
#   scp scripts/setup-decky-restart.sh steamdeck:~/
#   ssh -t steamdeck "bash setup-decky-restart.sh"
# Enter the deck user's password once when sudo prompts for it.
set -euo pipefail

PLUGIN_DIR="${DECK_PLUGINS_DIR:-/home/deck/homebrew/plugins}/xray-decky"
SUDOERS_FILE="/etc/sudoers.d/zzz-decky-restart"

RULES="deck ALL=(root) NOPASSWD: /usr/bin/chown -R deck\\:deck ${PLUGIN_DIR}
deck ALL=(root) NOPASSWD: /usr/bin/systemctl restart plugin_loader"

echo "Installing ${SUDOERS_FILE} (needs sudo password once)..."
echo "$RULES" | sudo tee "$SUDOERS_FILE" > /dev/null
sudo chmod 0440 "$SUDOERS_FILE"
sudo visudo -c -f "$SUDOERS_FILE"

echo "✅ Passwordless sudo configured for chown + plugin_loader restart."
echo "   Verify from your PC with:"
echo "   ssh steamdeck 'sudo -n /usr/bin/systemctl restart plugin_loader'"
