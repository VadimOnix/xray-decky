#!/bin/bash
# Build, zip and upload the plugin package to a Steam Deck over SSH.
#
# Nothing is hardcoded — configure via environment variables or an optional
# .deckdeployrc file in the repo root (gitignored, plain shell assignments):
#
#   DECK_HOST        ssh destination                  (default: steamdeck)
#   DECK_UPLOAD_DIR  where to place the zip on device (default: ~/Downloads)
#
# Name, version and zip filename come from package.json.
set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [ -f .deckdeployrc ]; then
  # shellcheck disable=SC1091
  source .deckdeployrc
fi

DECK_HOST="${DECK_HOST:-steamdeck}"
DECK_UPLOAD_DIR="${DECK_UPLOAD_DIR:-~/Downloads}"

PLUGIN_NAME="$(node -p "require('./package.json').name")"
PLUGIN_VERSION="$(node -p "require('./package.json').version")"
ZIP_NAME="${PLUGIN_NAME}-v${PLUGIN_VERSION}.zip"

echo -e "${BLUE}🔨 Building ${PLUGIN_NAME} v${PLUGIN_VERSION}...${NC}"
pnpm run build

echo -e "${BLUE}📦 Creating plugin package...${NC}"
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT
PLUGIN_DIR="$TEMP_DIR/$PLUGIN_NAME"

echo -e "${YELLOW}📋 Staging files...${NC}"
scripts/stage-plugin.sh "$PLUGIN_DIR"

echo -e "${YELLOW}📦 Creating ZIP archive...${NC}"
(cd "$TEMP_DIR" && zip -r "$ZIP_NAME" "$PLUGIN_NAME" > /dev/null)
ZIP_PATH="$TEMP_DIR/$ZIP_NAME"

ZIP_SIZE="$(du -h "$ZIP_PATH" | cut -f1)"
echo -e "${GREEN}✅ Created: $ZIP_NAME (${ZIP_SIZE})${NC}"

echo -e "${BLUE}🚀 Uploading to ${DECK_HOST}:${DECK_UPLOAD_DIR}/ ...${NC}"
if scp "$ZIP_PATH" "${DECK_HOST}:${DECK_UPLOAD_DIR}/"; then
  echo -e "${GREEN}✅ Uploaded ${ZIP_NAME} to ${DECK_UPLOAD_DIR} on ${DECK_HOST}${NC}"
  echo -e "${YELLOW}💡 To install:${NC}"
  echo -e "   1. Open Decky Loader on the Steam Deck"
  echo -e "   2. Settings → Developer → Install Plugin from URL / zip"
  echo -e "   3. Or unzip into the Decky plugins directory and restart plugin_loader"
else
  echo -e "${YELLOW}⚠️  Upload failed. ZIP kept at: ${ZIP_PATH}${NC}"
  # Keep the artifact for manual use despite the trap cleanup.
  cp "$ZIP_PATH" .
  echo -e "${YELLOW}   Copied to ./${ZIP_NAME}${NC}"
  exit 1
fi

echo -e "${GREEN}✨ Done!${NC}"
