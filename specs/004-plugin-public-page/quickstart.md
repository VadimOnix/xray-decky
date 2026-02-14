# Quickstart: Public Plugin Page (004-plugin-public-page)

**Branch**: `004-plugin-public-page` | **Date**: 2026-02-14

## What this feature delivers

A single **static public landing page** for the Xray Decky plugin: mobile-first, Steam Deck/SteamOS–style, native HTML/CSS with minimal or no JavaScript. The page presents the plugin name, purpose, platform, features, and how to install it.

## Where the code lives

- **Page and assets**: `docs/`
  - `index.html` — single page, semantic sections
  - `styles/main.css` — mobile-first, Steam Deck–inspired theme
  - `assets/` — hero image and feature visuals

## How to edit the page

1. Open `docs/index.html` for content (sections, text, image references).
2. Open `docs/styles/main.css` for layout and appearance (breakpoints, colors, typography).
3. Add or replace images in `docs/assets/` (hero, features). Keep `alt` text updated in HTML.
4. Keep content in sync with `plugin.json` (name, description) and README (features, install) when you change them.

## How to preview locally

1. Open `docs/index.html` in a browser (file:// or via a local static server).
2. Resize the window or use device toolbar (e.g. Chrome DevTools) to check 375px (mobile) and 1280px (desktop).
3. Optionally disable images or JavaScript to verify fallbacks (FR-008).

## How to publish (stable URL)

- **GitHub Pages**: Enable Pages for the repo, source = branch (e.g. `main`) and folder = **/docs**. The page will be at `https://<owner>.github.io/<repo>/`. Configure: Settings → Pages → Source: Deploy from a branch → Branch: main → Folder: /docs.
- **Other host**: Copy `docs/` (index.html, styles/, assets/) to any static host; ensure `index.html` is served at the chosen path and assets use relative paths.

## Optional: embed snippet

If you want a short embeddable block (e.g. for Gist or a blog):

- Create a Gist with a single file containing the snippet (plugin name, one sentence, platform, link to full page). Use the Gist’s embed URL where the host supports it.
- Or expose a fragment of the main page (e.g. `...#features`) and document the URL for embedding.

## Constraints (from plan)

- **Mobile-first**: Styles default to small viewport; use `min-width` media queries to enhance for larger screens.
- **Native HTML/CSS**: Prefer `<details>`/`<summary>` for expandable content; add JS only when HTML/CSS cannot do the job.
- **No secrets**: Do not put tokens, API keys, or user-specific paths in the page or in any snippet.
