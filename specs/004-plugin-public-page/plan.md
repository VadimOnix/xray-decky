# Implementation Plan: Public Plugin Page with Steam Deck/SteamOS Styling

**Branch**: `004-plugin-public-page` | **Date**: 2026-02-14 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/004-plugin-public-page/spec.md`  
**User constraints**: Mobile-first, web best practices, native HTML/CSS for UI, JavaScript only when CSS/HTML cannot achieve the interaction.

## Summary

Deliver a single public landing page for the Xray Decky plugin that presents name, purpose, platform, features, and install path. The page must be mobile-first, responsive (375px–1280px+), use Steam Deck/SteamOS-inspired visual design (dark theme, clear hierarchy), and include at least one hero image plus feature-related media. Implementation uses **native HTML5 and CSS3** (semantic markup, Flexbox/Grid, relative units, `<details>`/`<summary>` for expandable content); **JavaScript only** where interactivity cannot be achieved with HTML/CSS (e.g. copy-URL or future enhancements). The page is static, shareable via stable URL, and embeddable where the host supports it; no secrets or user-specific data.

## Technical Context

**Language/Version**: HTML5, CSS3; optional minimal JavaScript (ES5+ or ES module) only when necessary  
**Primary Dependencies**: None for core page (vanilla); optional no-JS build tool (e.g. copy/minify) only if needed  
**Storage**: N/A (static content)  
**Testing**: Manual visual and responsive checks; optional lightweight HTML/CSS validation or lighthouse  
**Target Platform**: Web browsers (mobile-first: 375px typical; desktop 1280px+); progressive enhancement for older browsers  
**Project Type**: Static web (single page)  
**Performance Goals**: First contentful paint &lt; 1.5s on 3G-like; page usable without JavaScript; images optimized (WebP with fallback, responsive srcset where useful)  
**Constraints**: No backend; no user data; JS only when HTML/CSS insufficient; assets legally safe (original or permitted)  
**Scale/Scope**: One page, one stable URL; 4–6 feature blocks; 1 hero + feature media set

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

This feature **adds a standalone static public page**; it does not change the Decky Loader plugin code, build, or distribution.

- **I. Standardized Project Structure**: Plugin structure unchanged. Static page lives in a dedicated folder `pages/` so plugin `src/`, `backend/`, `dist/` remain as-is.
- **II. Mandatory Metadata Files**: No change to plugin.json, package.json, LICENSE.
- **III. Frontend Development Standards**: Plugin frontend (React/Decky) unchanged. Public page is separate static HTML/CSS (no React/Node required for the page itself).
- **IV. Backend Development Patterns**: No backend for the public page.
- **V. Build & Distribution Requirements**: Plugin build (dist/index.js, etc.) unchanged. Public page is deployed separately (e.g. GitHub Pages or Gist); version in package.json not tied to page content.
- **VI. Security First**: Public page contains no secrets, tokens, or user paths; static content only.
- **VII. Semantic Versioning**: Plugin versioning unchanged; page content updates do not require package.json bump unless release process ties them.
- **VIII. Real Device Testing**: Plugin still tested on Steam Deck as today; public page is tested on browsers (mobile + desktop).

**Violations**: None. The public page is an additive artifact; Constitution applies to the plugin, which is not modified by this feature.

## Project Structure

### Documentation (this feature)

```text
specs/004-plugin-public-page/
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1 (page structure / embed)
└── tasks.md             # Phase 2 (/speckit.tasks)
```

### Source Code (repository root)

Static public page lives in `pages/` for GitHub Pages deployment (source: root).

```text
pages/                    # Public landing page (this feature)
├── index.html           # Single page, semantic sections
├── styles/
│   └── main.css         # Mobile-first, Steam Deck–style, minimal/no JS
├── assets/              # Images: hero, feature icons/graphics
│   ├── hero.*           # Hero/header image
│   └── features/        # Per-feature visuals
└── scripts/             # Optional build scripts (e.g. optimize-images.sh)

docs/
├── DEVELOPMENT.md
└── RELEASING.md
```

**Structure Decision**: One folder `pages/` with one HTML file, one main CSS file, and an assets subfolder. GitHub Pages: deploy from branch root → site at `https://<owner>.github.io/<repo>/pages/`. No build step required; optional minification available.

## Complexity Tracking

No Constitution violations. No entries required.
