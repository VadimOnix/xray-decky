# Data Model: Public Plugin Page (004-plugin-public-page)

**Branch**: `004-plugin-public-page` | **Date**: 2026-02-14

The public page is static content; there is no database or API. This document describes the **content entities** and **structure** that the page presents. Validation rules are derived from the feature spec (FR-001–FR-009) and success criteria.

---

## Entities

### Plugin identity (logical)

Represents what the page is about. Not stored in a DB; encoded in HTML and optionally in `plugin.json` for consistency.

| Attribute        | Description                              | Validation / source                |
|-----------------|------------------------------------------|------------------------------------|
| name            | Plugin display name                      | e.g. "Xray Decky"                  |
| purpose         | One-sentence description                 | Short, clear; no secrets           |
| platform        | Target platform text                     | "Steam Deck / Decky Loader"        |
| install_link    | URL or anchor to install steps           | Stable; no user-specific paths     |
| feature_list    | Ordered list of main features            | 4–6 items; matches plugin.json/README |

**Source**: Can be copied from `plugin.json` (name, description) and README (features, install) so the page stays in sync with the repo.

---

### Section (page structure)

The page is divided into semantic sections. Each section has a role and optional media.

| Section       | Role                         | Content / behavior                    |
|---------------|------------------------------|---------------------------------------|
| hero          | First impression             | Title, one-sentence purpose, hero image |
| features      | List of capabilities         | 4–6 feature blocks; each may have icon/image, title, short text |
| install       | How to get the plugin        | Steps or link to Plugin Store / README |
| footer        | Legal / links                | Optional: license, repo link, no secrets |

**Validation**: Hero and at least one feature block must be present (FR-001, FR-004). Install path or link must be present (FR-002).

---

### Media asset

Any image or short visual used on the page.

| Attribute   | Description                    | Validation                    |
|-------------|--------------------------------|-------------------------------|
| role        | hero \| feature \| other      | At least one hero, one set for features (FR-004, SC-002) |
| alt_text    | Accessible description        | Non-empty; meaningful (FR-008) |
| style       | Steam Deck/SteamOS-aligned     | Dark, clean; no unauthorized logos (FR-009) |
| format      | WebP with fallback preferred   | Web-appropriate; responsive if needed |

**State**: Static files in `docs/plugin-page/assets/`. No state transitions; content is fixed at publish time.

---

## Relationships

- **Page** has one **Plugin identity** (embedded in content).
- **Page** has ordered **Sections** (hero, features, install, footer).
- **Section** may have zero or more **Media assets** (e.g. hero has one image; each feature block may have one icon/image).

---

## No API or storage

There are no REST endpoints, no database, and no user data. The "data model" is the content structure of a single static HTML page and its assets. Updates are done by editing HTML/CSS and assets and redeploying.
