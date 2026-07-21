#!/bin/bash
# Prepare a release in one command:
#   scripts/prepare-release.sh <version>     e.g. 2.0.0-alpha.1
#
# - bumps "version" in package.json
# - rolls the CHANGELOG's [Unreleased] entries into a new dated
#   "## [<version>] - YYYY-MM-DD" section (leaving a fresh empty
#   [Unreleased] on top)
#
# Commit the result and merge it to master — the Auto Release workflow
# tags the commit and publishes the release (see docs/RELEASING.md).
set -euo pipefail

VERSION="${1:?Usage: $0 <version>   e.g. 2.0.0-alpha.1}"

if ! echo "$VERSION" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$'; then
  echo "❌ '$VERSION' is not a semver version (expected e.g. 2.0.0-alpha.1)" >&2
  exit 1
fi
if [ ! -f package.json ] || [ ! -f CHANGELOG.md ]; then
  echo "❌ Run from the repository root (package.json / CHANGELOG.md not found)." >&2
  exit 1
fi

CURRENT="$(node -p "require('./package.json').version")"
if [ "$CURRENT" = "$VERSION" ]; then
  echo "❌ package.json is already at ${VERSION}." >&2
  exit 1
fi
if grep -q "^## \[${VERSION}\]" CHANGELOG.md; then
  echo "❌ CHANGELOG.md already has a [${VERSION}] section." >&2
  exit 1
fi
if git rev-parse -q --verify "refs/tags/v${VERSION}" >/dev/null 2>&1; then
  echo "❌ Tag v${VERSION} already exists." >&2
  exit 1
fi
if ! grep -q "^## \[Unreleased\]" CHANGELOG.md; then
  echo "❌ CHANGELOG.md has no [Unreleased] section to roll." >&2
  exit 1
fi

# Bump package.json, preserving 2-space formatting and the trailing newline.
node -e "
  const fs = require('fs');
  const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
  pkg.version = '${VERSION}';
  fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2) + '\n');
"

# Roll [Unreleased] into the new dated section: everything that was under
# [Unreleased] now sits under the new version header. perl, not sed -i:
# BSD sed (macOS) rejects GNU's zero-arg -i and \n in replacements.
DATE="$(date +%Y-%m-%d)"
perl -0pi -e "s/^## \[Unreleased\]\n/## [Unreleased]\n\n## [${VERSION}] - ${DATE}\n/m" CHANGELOG.md

echo "✅ ${CURRENT} → ${VERSION}"
echo "   - package.json bumped"
echo "   - CHANGELOG.md: [Unreleased] rolled into [${VERSION}] - ${DATE}"
echo ""
echo "Review the diff, then commit and merge to master:"
echo "   git diff package.json CHANGELOG.md"
echo "Merging the bump to master tags v${VERSION} and publishes the release."
