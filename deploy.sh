#!/bin/bash
# Build and deploy a development version to a Steam Deck over SSH.
#
# Nothing is hardcoded — configure via environment variables or an optional
# .deckdeployrc file in the repo root (gitignored, plain shell assignments):
#
#   DECK_HOST         ssh destination            (default: steamdeck)
#   DECK_PLUGINS_DIR  Decky plugins dir on device (default: /home/deck/homebrew/plugins)
#   DECK_RESTART      1 = restart plugin_loader after sync (default: 0;
#                     needs sudo on the device — passwordless sudo for
#                     'systemctl restart plugin_loader' makes this seamless)
#
# The plugin name comes from package.json. The device's bin/ directory
# (self-healed xray-core) is preserved across deploys.
set -euo pipefail

if [ -f .deckdeployrc ]; then
  # shellcheck disable=SC1091
  source .deckdeployrc
fi

DECK_HOST="${DECK_HOST:-steamdeck}"
DECK_PLUGINS_DIR="${DECK_PLUGINS_DIR:-/home/deck/homebrew/plugins}"
DECK_RESTART="${DECK_RESTART:-0}"

PLUGIN_NAME="$(node -p "require('./package.json').name")"
PLUGIN_VERSION="$(node -p "require('./package.json').version")"
REMOTE_DIR="${DECK_PLUGINS_DIR}/${PLUGIN_NAME}"

echo "🔨 Building ${PLUGIN_NAME} v${PLUGIN_VERSION}..."
pnpm run build

echo "📦 Staging files..."
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT
PLUGIN_DIR="$TEMP_DIR/$PLUGIN_NAME"
scripts/stage-plugin.sh "$PLUGIN_DIR"

echo "🚀 Deploying to ${DECK_HOST}:${REMOTE_DIR}/ ..."
# --exclude bin/ keeps the core the device already downloaded (self-heal
# re-fetches it otherwise, which needs network on the Deck).
rsync -avz --delete --exclude 'bin/' --progress \
  --timeout=30 \
  --partial \
  -e "ssh -o ServerAliveInterval=10 -o ServerAliveCountMax=3" \
  "$PLUGIN_DIR/" "${DECK_HOST}:${REMOTE_DIR}/"

if [ "$DECK_RESTART" = "1" ]; then
  echo "🔄 Restarting plugin_loader on ${DECK_HOST}..."
  ssh "$DECK_HOST" "sudo systemctl restart plugin_loader"
else
  echo "💡 Restart Decky to pick up the new build:"
  echo "   ssh ${DECK_HOST} 'sudo systemctl restart plugin_loader'"
  echo "   (or set DECK_RESTART=1 to do this automatically)"
fi

echo "✅ Deployment complete!"
