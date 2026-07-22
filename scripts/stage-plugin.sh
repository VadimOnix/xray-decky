#!/bin/bash
# Stage the plugin's runtime tree into a destination directory.
#
# Single source of truth for "which files ship to the Deck" — used by
# deploy.sh, package-and-deploy.sh and scripts/package-local.sh so the
# file set can't drift between them. (The release workflow mirrors this
# list in .github/workflows/release.yml.)
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
if [ ! -d backend/static ]; then
  echo "❌ backend/static missing — the embedded web server would not start on device." >&2
  exit 1
fi

mkdir -p "$DEST"

# Frontend bundle + plugin metadata.
cp -r dist "$DEST/"
cp package.json plugin.json main.py LICENSE.md "$DEST/"
[ -f README.md ] && cp README.md "$DEST/"

# Network recovery script (run manually if the Deck loses connectivity).
cp scripts/recover.sh "$DEST/"

# Backend package: python sources (Decky CLI py_modules/ layout) and
# pinned-version metadata (read at runtime by the self-heal downloader).
cp -r py_modules "$DEST/"
# Strip dev-machine cruft that cp -r would otherwise ship to the Deck.
find "$DEST/py_modules" -name '__pycache__' -type d -prune -exec rm -rf {} +
find "$DEST/py_modules" -name '.DS_Store' -delete

# Static web panel.
mkdir -p "$DEST/backend"
cp -r backend/static "$DEST/backend/"

# Core binaries, when present locally (backend/out -> bin/). Optional: the
# plugin self-heals by downloading its pinned core on first start.
if [ -d backend/out ] && [ -n "$(ls -A backend/out 2>/dev/null)" ]; then
  mkdir -p "$DEST/bin"
  cp -r backend/out/. "$DEST/bin/"
fi
