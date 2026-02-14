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

4. **(Optional) Update `XRAY_VERSION`** in `.github/workflows/release.yml` if a new xray-core release is available

## Creating a Release

### Step 1: Create and push the tag

```bash
# Replace 1.0.0 with your version
git tag v1.0.0
git push origin v1.0.0
```

That's it. Pushing the tag will trigger the release workflow automatically.

### Step 2: Monitor the workflow

1. Go to **Actions** tab on GitHub
2. Find the **Release** workflow run for your tag
3. Wait for it to complete
4. The release will appear under **Releases** with the ZIP artifact attached

### Step 3: Optional — Edit the release

- Add release notes or description
- Attach additional files
- Mark as pre-release for beta/alpha versions

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
