# Release Process

This document describes how to create a release of xray-decky. The project uses [Semantic Versioning](https://semver.org/) and [Keep a Changelog](https://keepachangelog.com/).

## How the Release Workflow Works

The release is automated via [`.github/workflows/release.yml`](../.github/workflows/release.yml). The workflow **triggers only on tags that match `v*`** (e.g. `v1.0.0`, `v1.2.3`, `v2.0.0-beta.1`).

### Important: Tag Format

- ✅ Correct: `v1.0.0`, `v1.2.3`, `v2.0.0-beta.1`
- ❌ Wrong: `1.0.0` (without the `v` prefix) — the workflow will **not** run

When you push a tag like `v1.0.0`, the workflow:

1. Checks out the code
2. Installs dependencies and builds the plugin (`pnpm install && pnpm run build`)
3. Downloads xray-core binary (version in `XRAY_VERSION` env in workflow)
4. Packages the plugin into a ZIP: `dist/`, `package.json`, `plugin.json`, `main.py`, `LICENSE.md`, `README.md`, `backend/`, and the xray-core binary
5. Creates a GitHub Release with the ZIP attached and auto-generated release notes

## Pre-Release Checklist

Before creating a release tag:

1. **Update `CHANGELOG.md`**
   - Move entries from `[Unreleased]` to a new version section
   - Use date in `YYYY-MM-DD` format
   - Follow [Keep a Changelog](https://keepachangelog.com/) format

2. **Update version in `package.json`**
   - Ensure `version` matches the release (e.g. `"1.0.0"`)

3. **Commit and push** all changes to the default branch
   - Ensure CI passes
   - Ensure the commit you're tagging is the one you want released

4. **(Optional) Update the xray-core pin** in `backend/src/xray_version.json` if a new core release is available (the release workflow bundles whatever is pinned there)

## Creating a Release

### The automated way (default)

Releases are fully automated by `.github/workflows/auto-release.yml`:

1. Run `scripts/prepare-release.sh <version>` (e.g. `2.0.0-alpha.1`) — it bumps
   `package.json` and rolls the `[Unreleased]` CHANGELOG entries into a new
   dated version section in one step. Review the diff and open a PR.
2. Merge it to `master`.

CI refuses a `package.json` version that has no matching CHANGELOG section
(unless that version is already tagged), so a release can't ship without its
changelog slice. Pre-release versions (`-alpha`/`-beta`/`-rc`) additionally
get a prominent work-in-progress warning on top of the GitHub release notes.

On the push to `master`, the Auto Release workflow sees that `package.json`
now carries a version with no matching `v<version>` tag, creates the tag on
that commit, and dispatches the **Release** workflow, which builds the ZIP
(with the pinned xray-core bundled) and publishes the GitHub Release.
Versions containing a `-` (e.g. `2.0.0-alpha.1`) are automatically marked
as **pre-releases**.

Merging anything that doesn't change the `package.json` version never
releases — the version bump is the single deliberate release act.

### The manual way (still works)

```bash
# Replace 1.0.0 with your version (must match package.json)
git tag v1.0.0
git push origin v1.0.0
```

A manually pushed `v*` tag triggers the Release workflow directly.

### Monitor the workflow

1. Go to **Actions** tab on GitHub
2. Find the **Release** workflow run for your tag
3. Wait for it to complete
4. The release will appear under **Releases** with the ZIP artifact attached

## If You Created the Wrong Tag

If you pushed a tag without the `v` prefix (e.g. `1.0.0`):

```bash
# Delete local tag
git tag -d 1.0.0

# Delete remote tag
git push origin :refs/tags/1.0.0

# Create and push correct tag
git tag v1.0.0
git push origin v1.0.0
```

## Version Examples

| Tag          | Workflow runs? | Notes                    |
|-------------|----------------|--------------------------|
| `v1.0.0`    | ✅ Yes         | Standard release         |
| `v1.2.3`    | ✅ Yes         | Patch release            |
| `v2.0.0-beta.1` | ✅ Yes     | Pre-release              |
| `1.0.0`     | ❌ No          | Missing `v` prefix       |
| `release-1.0` | ❌ No        | Doesn't match `v*`       |
