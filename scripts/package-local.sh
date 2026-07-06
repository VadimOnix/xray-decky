#!/bin/bash
# Build and zip the plugin locally (no device involved).
#
# The zip name is derived from package.json — nothing hardcoded:
#   <name>-v<version>.zip in the repo root.
set -euo pipefail

PLUGIN_NAME="$(node -p "require('./package.json').name")"
PLUGIN_VERSION="$(node -p "require('./package.json').version")"
ZIP_NAME="${PLUGIN_NAME}-v${PLUGIN_VERSION}.zip"

echo "🔨 Building ${PLUGIN_NAME} v${PLUGIN_VERSION}..."
pnpm run build

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT
PLUGIN_DIR="$TEMP_DIR/$PLUGIN_NAME"

echo "📦 Staging files..."
scripts/stage-plugin.sh "$PLUGIN_DIR"

echo "📦 Creating ZIP archive..."
rm -f "$ZIP_NAME"
(cd "$TEMP_DIR" && zip -r "$ZIP_NAME" "$PLUGIN_NAME" > /dev/null)
mv "$TEMP_DIR/$ZIP_NAME" .

echo "✅ ZIP created: ${ZIP_NAME} ($(du -h "$ZIP_NAME" | cut -f1))"
