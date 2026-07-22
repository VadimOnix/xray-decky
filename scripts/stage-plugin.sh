#!/bin/bash
# Stage the plugin's runtime tree into a destination directory.
#
# Single source of truth for "which files ship to the Deck" — used by
# deploy.sh, package-and-deploy.sh, scripts/package-local.sh, AND the
# release workflow (.github/workflows/release.yml), so the file set
# can't drift between any of them.
#
# Usage: scripts/stage-plugin.sh <dest-dir>
#   <dest-dir> is created if missing; files are staged directly into it
#   (callers decide the wrapping <plugin-name>/ directory).
#
# Must be run from the repository root after `pnpm run build`.
set -euo pipefail

if [ $# -ne 1 ] || [ -z "$1" ]; then
  echo "Usage: $0 <dest-dir>" >&2
  exit 64
fi
DEST="$1"

if [ ! -d dist ]; then
  echo "❌ dist/ missing — run 'pnpm run build' first." >&2
  exit 1
fi
if [ ! -d py_modules/backend/src ]; then
  echo "❌ py_modules/backend/src missing — backend code not found." >&2
  exit 1
fi
if [ ! -d defaults/static ]; then
  echo "❌ defaults/static missing — the embedded web server would not start on device." >&2
  exit 1
fi

mkdir -p "$DEST"

# Frontend bundle + plugin metadata.
cp -r dist "$DEST/"
cp package.json plugin.json main.py LICENSE "$DEST/"
[ -f README.md ] && cp README.md "$DEST/"

# Network recovery script (run manually if the Deck loses connectivity).
cp scripts/recover.sh "$DEST/"

# Backend package: python sources (Decky CLI py_modules/ layout) and
# pinned-version metadata (read at runtime by the self-heal downloader).
cp -r py_modules "$DEST/"
# Strip dev-machine cruft that cp -r would otherwise ship to the Deck.
find "$DEST/py_modules" -name '__pycache__' -type d -prune -exec rm -rf {} +

# Static web panel (Decky CLI layout: defaults/ contents land at plugin
# root, so this ships as <plugin>/static/). mkdir + trailing-slash cp keeps
# this safe to re-run into an existing $DEST without nesting static/static.
mkdir -p "$DEST/static"
cp -r defaults/static/. "$DEST/static/"

# Core binaries, when present locally (bin/ -> bin/). Optional: the plugin
# self-heals by downloading its pinned core on first start.
if [ -d bin ] && [ -n "$(ls -A bin 2>/dev/null)" ]; then
  mkdir -p "$DEST/bin"
  cp -r bin/. "$DEST/bin/"
fi

# Strip dev-machine cruft (covers dist/, py_modules/, static/ in one pass).
find "$DEST" -name '.DS_Store' -delete
