#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get name and version from package.json
PLUGIN_NAME=$(node -p "require('./package.json').name")
PLUGIN_VERSION=$(node -p "require('./package.json').version")
ZIP_NAME="${PLUGIN_NAME}-v${PLUGIN_VERSION}.zip"

echo -e "${BLUE}🔨 Building project...${NC}"
pnpm run build

echo -e "${BLUE}📦 Creating plugin package...${NC}"

# Create temporary directory for packaging
TEMP_DIR=$(mktemp -d)
PLUGIN_DIR="$TEMP_DIR/$PLUGIN_NAME"

mkdir -p "$PLUGIN_DIR"

# Copy required files per DeckBrew structure
echo -e "${YELLOW}📋 Copying files...${NC}"

# Required files
cp -r dist "$PLUGIN_DIR/"
cp package.json "$PLUGIN_DIR/"
cp plugin.json "$PLUGIN_DIR/"
cp main.py "$PLUGIN_DIR/"
cp LICENSE.md "$PLUGIN_DIR/"

# Optional files
if [ -f README.md ]; then
  cp README.md "$PLUGIN_DIR/"
fi

# Backend and import server: backend/src/*.py (cert_utils, import_server, …), backend/static (import.html, import.css)
if [ ! -d backend/src ] || [ ! -d backend/static ]; then
  echo -e "${YELLOW}❌ backend/src or backend/static missing. Import server will not start on device.${NC}"
  exit 1
fi
mkdir -p "$PLUGIN_DIR/backend/src"
cp backend/__init__.py "$PLUGIN_DIR/backend/" 2>/dev/null || echo "# Backend package" > "$PLUGIN_DIR/backend/__init__.py"
cp backend/src/__init__.py "$PLUGIN_DIR/backend/src/" 2>/dev/null || echo "# Backend src package" > "$PLUGIN_DIR/backend/src/__init__.py"
cp backend/src/*.py "$PLUGIN_DIR/backend/src/"
mkdir -p "$PLUGIN_DIR/backend"
cp -r backend/static "$PLUGIN_DIR/backend/"

# Backend binaries (if present)
if [ -d backend/out ] && [ "$(ls -A backend/out 2>/dev/null)" ]; then
  mkdir -p "$PLUGIN_DIR/bin"
  cp -r backend/out/* "$PLUGIN_DIR/bin/" 2>/dev/null || true
fi

# Create ZIP archive
echo -e "${YELLOW}📦 Creating ZIP archive...${NC}"
cd "$TEMP_DIR"
zip -r "$ZIP_NAME" "$PLUGIN_NAME" > /dev/null
ZIP_PATH="$TEMP_DIR/$ZIP_NAME"

# Show archive size
ZIP_SIZE=$(du -h "$ZIP_PATH" | cut -f1)
echo -e "${GREEN}✅ Created: $ZIP_NAME (${ZIP_SIZE})${NC}"

# Upload to Steam Deck
echo -e "${BLUE}🚀 Uploading to Steam Deck...${NC}"
scp "$ZIP_PATH" steamdeck:~/Downloads/

if [ $? -eq 0 ]; then
  echo -e "${GREEN}✅ Successfully uploaded to ~/Downloads/$ZIP_NAME on Steam Deck${NC}"
  echo -e "${YELLOW}💡 To install:${NC}"
  echo -e "   1. Open Decky Loader on Steam Deck"
  echo -e "   2. Go to Settings → Developer → Install Plugin from URL"
  echo -e "   3. Or manually copy from ~/Downloads to ~/homebrew/plugins/$PLUGIN_NAME"
else
  echo -e "${YELLOW}⚠️  Upload failed. ZIP file saved at: $ZIP_PATH${NC}"
  exit 1
fi

# Cleanup
rm -rf "$TEMP_DIR"

echo -e "${GREEN}✨ Done!${NC}"
