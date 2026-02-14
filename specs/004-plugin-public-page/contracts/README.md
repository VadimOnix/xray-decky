# Contracts: Public Plugin Page (004-plugin-public-page)

**Branch**: `004-plugin-public-page` | **Date**: 2026-02-14

This feature has **no REST or GraphQL API**. The "contracts" here define the **expected structure of the public page** and, if used, the **embed snippet** so that consumers (humans or embed contexts) know what to expect.

---

## 1. Page structure contract

The single HTML page MUST expose the following structure so that spec FR-001, FR-002, and SC-001 are met:

- **Document**: One `index.html` with semantic regions.
- **Required regions** (in order):
  1. **Header/Hero**: Plugin name, one-sentence purpose, platform (Steam Deck / Decky Loader), and one hero/header image (with `alt`).
  2. **Main**: At least one section listing primary features (4–6 items); each item may have title, short description, and optional image/icon.
  3. **Install**: Section or block with installation steps or a clear link to install (Plugin Store, README, or equivalent).
  4. **Footer** (optional): Repo link, license; no secrets or user paths.

- **Accessibility**: Critical text (name, purpose, install link) MUST be in plain text or static markup so the page works without JavaScript and when images fail (FR-008).

---

## 2. Embed snippet contract (optional)

If the team provides an embeddable fragment (e.g. for Gist or blog):

- **Format**: Either a stable URL to a fragment (e.g. `.../pages/#features`) or a self-contained HTML snippet (no scripts that depend on host domain).
- **Content**: Snippet MUST contain only public, non-sensitive content (FR-007). Expected fields: plugin name, one-sentence description, platform, and link to full page or install.
- **Rendering**: When embedded in a context that supports iframe or script-based Gist embed, the fragment MUST render without errors and remain readable (FR-006).

No formal API schema (OpenAPI/GraphQL) is required for this feature.
