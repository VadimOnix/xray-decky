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
if [ ! -d backend/src ] || [ ! -d backend/static ]; then
  echo "❌ backend/src or backend/static missing — the embedded web server would not start on device." >&2
  exit 1
fi

mkdir -p "$DEST"

# Frontend bundle + plugin metadata.
cp -r dist "$DEST/"
cp package.json plugin.json main.py LICENSE.md "$DEST/"
[ -f README.md ] && cp README.md "$DEST/"

# Network recovery script (run manually if the Deck loses connectivity).
cp scripts/recover.sh "$DEST/"

# Backend package: python sources, pinned-version metadata (read at runtime
# by the self-heal downloader) and the static web panel.
mkdir -p "$DEST/backend/src"
if [ -f backend/__init__.py ]; then
  cp backend/__init__.py "$DEST/backend/"
else
  echo "# Backend package" > "$DEST/backend/__init__.py"
fi
if [ -f backend/src/__init__.py ]; then
  cp backend/src/__init__.py "$DEST/backend/src/"
else
  echo "# Backend src package" > "$DEST/backend/src/__init__.py"
fi
cp backend/src/*.py "$DEST/backend/src/"
cp backend/src/*.json "$DEST/backend/src/"
cp -r backend/static "$DEST/backend/"

# Core binaries, when present locally (backend/out -> bin/). Optional: the
# plugin self-heals by downloading its pinned core on first start.
if [ -d backend/out ] && [ -n "$(ls -A backend/out 2>/dev/null)" ]; then
  mkdir -p "$DEST/bin"
  cp -r backend/out/. "$DEST/bin/"
fi
