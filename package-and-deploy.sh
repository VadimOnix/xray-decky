#!/bin/bash
set -e

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Получаем имя и версию из package.json
PLUGIN_NAME=$(node -p "require('./package.json').name")
PLUGIN_VERSION=$(node -p "require('./package.json').version")
ZIP_NAME="${PLUGIN_NAME}-v${PLUGIN_VERSION}.zip"

echo -e "${BLUE}🔨 Building project...${NC}"
pnpm run build

echo -e "${BLUE}📦 Creating plugin package...${NC}"

# Создаем временную директорию для упаковки
TEMP_DIR=$(mktemp -d)
PLUGIN_DIR="$TEMP_DIR/$PLUGIN_NAME"

mkdir -p "$PLUGIN_DIR"

# Копируем необходимые файлы согласно структуре DeckBrew
echo -e "${YELLOW}📋 Copying files...${NC}"

# Обязательные файлы
cp -r dist "$PLUGIN_DIR/"
cp package.json "$PLUGIN_DIR/"
cp plugin.json "$PLUGIN_DIR/"
cp main.py "$PLUGIN_DIR/"
cp LICENSE.md "$PLUGIN_DIR/"

# Опциональные файлы
if [ -f README.md ]; then
  cp README.md "$PLUGIN_DIR/"
fi

# Backend исходники
if [ -d backend/src ]; then
  mkdir -p "$PLUGIN_DIR/backend"
  cp -r backend/src "$PLUGIN_DIR/backend/"
fi

# Backend бинарники (если есть)
if [ -d backend/out ] && [ "$(ls -A backend/out 2>/dev/null)" ]; then
  mkdir -p "$PLUGIN_DIR/bin"
  cp -r backend/out/* "$PLUGIN_DIR/bin/" 2>/dev/null || true
fi

# Создаем ZIP архив
echo -e "${YELLOW}📦 Creating ZIP archive...${NC}"
cd "$TEMP_DIR"
zip -r "$ZIP_NAME" "$PLUGIN_NAME" > /dev/null
ZIP_PATH="$TEMP_DIR/$ZIP_NAME"

# Показываем размер архива
ZIP_SIZE=$(du -h "$ZIP_PATH" | cut -f1)
echo -e "${GREEN}✅ Created: $ZIP_NAME (${ZIP_SIZE})${NC}"

# Отправляем на Steam Deck
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

# Очистка
rm -rf "$TEMP_DIR"

echo -e "${GREEN}✨ Done!${NC}"
