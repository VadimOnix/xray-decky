---
name: decky-release
description: Release flow for this plugin — prepare-release.sh, CHANGELOG rules, auto-release on version bump, v-prefixed tags, zip packaging, and the two supported install channels (installer script + release zip; the Decky Plugin Store is not one). Use when cutting a release, bumping the version, editing CHANGELOG.md, fixing a broken/wrong tag, or writing install instructions.
---

# Releasing xray-decky

Canonical doc: `docs/RELEASING.md`. SemVer + Keep a Changelog.

## The one rule

**A `package.json` version bump merged to `master` IS the release.** `auto-release.yml` sees a version with no matching `v<version>` tag, creates the tag, and dispatches the Release workflow (build → zip with pinned xray-core → GitHub Release). Merges that don't change the version never release.

## Standard flow

```bash
scripts/prepare-release.sh 2.4.0        # bumps package.json + rolls [Unreleased] → dated section
```

Review diff → PR → merge to `master`. Done.

Guard rails:
- CI **fails** if `package.json` has a version with no matching `CHANGELOG.md` section (unless already tagged) — a release can't ship without its changelog slice.
- Versions containing `-` (`2.4.0-alpha.1`) are auto-marked pre-release and get a WIP warning in release notes.
- Ongoing work goes under `[Unreleased]` in Keep a Changelog categories (Added/Changed/Fixed/…), dates `YYYY-MM-DD`.

## Manual tag (fallback)

```bash
git tag v1.0.0 && git push origin v1.0.0   # must match package.json version
```

Tag format `v*` is mandatory — `1.0.0` without prefix silently does nothing. Wrong tag cleanup: `git tag -d 1.0.0 && git push origin :refs/tags/1.0.0`, then retag correctly.

## What ships

Zip staged by `scripts/stage-plugin.sh`: `dist/`, `package.json`, `plugin.json`, `main.py`, `py_modules/`, `static/` (web panel), `LICENSE`, `README.md`, plus xray-core binary + geo data under `bin/` (version pinned in `py_modules/backend/src/xray_version.json` — update the pin before release if a new core is out).

## Decky Plugin Store — not a distribution channel

The Decky Loader maintainers declined to list this plugin over GPL licensing concerns around the bundled/downloaded proxy cores. **Do not add store-install instructions to the READMEs, the site or release notes.** The two supported channels are the installer script (`scripts/install-xray-decky.sh`, plus the `.desktop` one-click wrapper) and the release zip via Decky → Settings → Developer → Install Plugin from URL.

`plugin.json` → `publish` is kept as plain plugin metadata; it no longer feeds a store listing.
