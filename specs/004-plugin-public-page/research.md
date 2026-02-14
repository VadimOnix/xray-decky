# Research: Public Plugin Page (004-plugin-public-page)

**Branch**: `004-plugin-public-page` | **Date**: 2026-02-14

## 1. Mobile-first and responsive best practices

**Decision**: Design and implement the page for the smallest viewport first (e.g. 320px–375px), then progressively enhance with `min-width` media queries for tablet and desktop. Use fluid layouts (Flexbox and/or CSS Grid), relative units (rem, em, %, clamp()), and avoid fixed pixel widths for content.

**Rationale**: Mobile-first ensures core content and actions are usable on small screens; scaling up is easier than retrofitting mobile after desktop. Aligns with user constraint "mobile first" and spec SC-004 (readable at 375px and 1280px).

**Alternatives considered**: Desktop-first with max-width media queries was rejected because it often leads to cramped or overflow issues on mobile and contradicts the requested mobile-first approach.

---

## 2. Native HTML and CSS for UI; JavaScript only when necessary

**Decision**: Use semantic HTML5 (`<header>`, `<main>`, `<section>`, `<article>`, `<nav>`, `<footer>`) and modern CSS for layout and interactivity. Use `<details>`/`<summary>` for expandable sections (e.g. install steps, FAQ) so accordion-like behavior works without JS. Use `:focus-visible`, `@media (prefers-reduced-motion)`, and `scroll-margin` for accessibility. Introduce JavaScript only for behaviors that cannot be achieved with HTML/CSS (e.g. copy-URL-to-clipboard if desired; optional).

**Rationale**: Reduces payload, improves resilience when JS is blocked or fails, and matches the user constraint "elements interface native modern HTML and CSS, JS only when impossible with CSS and HTML." Native `<details>`/`<summary>` is well-supported and accessible.

**Alternatives considered**: JS-driven accordions or SPA framework were rejected for this single static page to keep the stack minimal and avoid dependency on React/Node for the page itself.

---

## 3. Steam Deck / SteamOS visual style (public interpretation)

**Decision**: Apply a dark theme inspired by public Steam/Steam Deck branding: dark background (#1b2838 or similar), lighter card/surface (#2a475e), accent for links and highlights (e.g. #66c0f4 blue or warm accent). Use clear typographic hierarchy (single sans-serif stack, e.g. system-ui or a single webfont), sufficient contrast (WCAG AA), and section/card layout that feels "deck-friendly" (rounded corners, subtle shadows). Do not use official Valve/Steam logos or assets without permission; use only style inspiration (colors, density, hierarchy).

**Rationale**: Spec FR-003 and FR-004 require visual design consistent with Steam Deck/SteamOS and media that match that style. Public brand guidelines and community themes indicate dark UI with blue/gray palette and clear hierarchy.

**Alternatives considered**: Generic light theme was rejected because the spec explicitly asks for Steam Deck/SteamOS styling. Using only public color references and no proprietary logos keeps the page legally safe (spec FR-009, Assumptions).

---

## 4. Hosting and URL stability

**Decision**: Prefer hosting that provides a stable, shareable URL (e.g. GitHub Pages from `docs/` or from a branch, or a dedicated Gist for an embeddable snippet). The implementation will be static files (HTML/CSS/assets) so they can be deployed to any static host. No dynamic server or API required.

**Rationale**: Spec FR-005 and FR-006 require a stable URL and optional embedding. Static hosting is sufficient and keeps the system simple (no backend, no secrets).

**Alternatives considered**: In-repo only without deployment was rejected because the spec requires the page to be "reachable" and "shareable"; at least one deployment path (e.g. GitHub Pages) should be documented in quickstart.

---

## 5. Images and media

**Decision**: Provide at least one hero/header image and one set of feature-related visuals (icons or images). Use modern formats (e.g. WebP with JPEG/PNG fallback via `<picture>` or fallback `src`), `width`/`height` to avoid layout shift, and `alt` text for accessibility. Prefer original or clearly licensed assets; style must align with Steam Deck/SteamOS (dark, clean, device or abstract).

**Rationale**: FR-004 and SC-002 require hero and feature visuals; FR-008 and edge cases require graceful degradation (placeholders/alt) when media fails.

**Alternatives considered**: Text-only page was rejected per spec. Relying on external CDN images without fallbacks was rejected for resilience.

---

## 6. Gist best practices (for shareability and embed)

**Decision**: If a Gist is used for an embeddable snippet (e.g. short description or install snippet), use a single-purpose Gist with a clear description and stable URL; support embed via GitHub’s script tag or iframe where applicable. The main page can still be full HTML in repo; Gist is optional for "copy-paste" or embed use cases.

**Rationale**: Spec and assumptions reference Gist best practices (clear description, stable URL, optional embed). The primary deliverable is the full public page; Gist is one way to expose a fragment for embedding, not a requirement to host the entire page as a Gist.

**Alternatives considered**: Hosting the entire page only as a Gist was rejected because a single HTML file in a Gist is less flexible for multi-file assets (CSS, images) and GitHub Pages or similar is better for the full landing experience.
