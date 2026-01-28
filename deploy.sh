#!/bin/bash
set -e

echo "🔨 Building project..."
pnpm run build

echo "📦 Preparing files for deployment..."

# Создаем временную директорию для деплоя
TEMP_DIR=$(mktemp -d)
PLUGIN_DIR="$TEMP_DIR/xray-decky"

mkdir -p "$PLUGIN_DIR"

# Копируем только необходимые файлы
echo "📋 Copying files..."
cp -r dist "$PLUGIN_DIR/"
cp package.json plugin.json main.py LICENSE.md "$PLUGIN_DIR/"
mkdir -p "$PLUGIN_DIR/backend"
cp -r backend/src "$PLUGIN_DIR/backend/"

echo "🚀 Deploying to Steam Deck..."
rsync -avz --delete --progress \
  --timeout=30 \
  --partial \
  -e "ssh -o ServerAliveInterval=10 -o ServerAliveCountMax=3" \
  "$PLUGIN_DIR/" steamdeck:/home/deck/homebrew/plugins/xray-decky/

echo "✅ Deployment complete!"
rm -rf "$TEMP_DIR"
