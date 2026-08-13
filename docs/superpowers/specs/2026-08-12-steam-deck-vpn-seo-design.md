# Steam Deck VPN SEO — Design

**Date:** 2026-08-12
**Status:** Approved (design review passed)
**Goal:** Rank the repository and its GitHub Pages site for `steam deck vpn` and
related queries in both GitHub search and Google/Yandex.

## Problem

The query `steam deck vpn` currently surfaces competitors
(`amnezia-vpn/amnezia-client` discussion #2180, `denmrnngp-cloud/hiddify-steam-deck-vpn`)
above this project. Root cause: the word **"VPN" appears nowhere** in the repo
name, description, topics, README, or site metadata. GitHub search requires all
query terms to match, so the repo is **entirely absent** from GitHub search
results for the query. "SteamDeck" (one word, in the description) does not
tokenize-match "steam deck" (two words). The competitor repo contains the full
query in its name and carries 20 keyword topics.

## Positioning decision (approved)

Hybrid **"VPN & Proxy client"** branding. Technically honest: TUN mode routes
all system traffic through a virtual interface — functionally a VPN tunnel.
"Proxy" remains in copy where precision matters. Repo is **not** renamed.

## Scope

1. **Repo metadata** (via `gh api`):
   - Description → `VPN & proxy client for Steam Deck — Decky Loader plugin.
     VLESS, VMess, Trojan, Shadowsocks, Hysteria2, TUIC · TUN mode for Gaming
     Mode · subscriptions · kill switch`
   - Topics → exactly 20 (GitHub max): keep `decky-loader, decky-plugin,
     steamdeck, vless, vless-reality, xray`; add `vpn, vpn-client, steam-deck,
     steam-deck-vpn, steamos, steamos-vpn, game-mode, sing-box, hysteria2,
     tuic, shadowsocks, trojan, v2ray, reality`.

2. **README**
   - H1 → `Xray Decky — VPN & Proxy Client for Steam Deck`.
   - First paragraph rewritten around search phrasing ("VPN for Steam Deck
     Gaming Mode"), with the honest "proxy-based VPN via TUN" framing.
   - Language switcher row at top: EN | Русский | 中文 | فارسی | Español →
     `README.ru.md`, `README.zh-CN.md`, `README.fa.md`, `README.es.md` (repo
     root). Translations mirror the full README.
   - `plugin.json` description gains "VPN" wording (feeds the Decky Store
     listing).

3. **Site migration to Astro with i18n** (approved over static per-language
   copies)
   - New `site/` directory: Astro project (pnpm, matching repo ecosystem).
     Existing hand-written HTML/CSS/JS ported near-verbatim into an Astro
     layout + components. Visual design unchanged.
   - Locale routes: `/` (en, default, no prefix), `/ru/`, `/zh/`, `/fa/`
     (RTL), `/es/`. `hreflang` alternates + `x-default`, per-page canonical,
     `@astrojs/sitemap`, `robots.txt`.
   - Per-locale SEO head: title `Xray Decky — VPN & Proxy Client for Steam
     Deck` (localized), meta description, Open Graph + Twitter cards, JSON-LD
     `SoftwareApplication` and `FAQPage`.
   - New guide page per locale: **"How to set up a VPN on Steam Deck"** —
     step-by-step (install Decky Loader → install plugin → import
     subscription → enable TUN → verify), targeting long-tail queries
     ("steam deck vpn gaming mode", "vpn on steamos without desktop mode").
   - Landing FAQ section extended with search-phrased questions ("Does the
     Steam Deck support a VPN?", "How do I use a VPN in Gaming Mode?").
   - Changelog page stays EN-only, ported as-is.
   - Deploy: new `.github/workflows/pages.yml` builds `site/` and publishes
     via `actions/deploy-pages`; Pages source switches from legacy
     `master:/docs` to workflow builds. Old site files (`docs/index.html`,
     `docs/changelog.html`, `docs/styles/`, `docs/assets/`, `docs/scripts/`)
     are absorbed into `site/` and deleted from `docs/`. Dev markdown docs
     (`docs/DEVELOPMENT.md`, `docs/RELEASING.md`, `docs/ROADMAP.md`,
     `docs/README.md`) stay put — they are linked as repo files, not web
     pages.

4. **Translations**
   - RU, ZH (Simplified), FA, ES authored in this effort; RU proofread by the
     maintainer. EN is the source of truth; translations refresh on major
     releases only.

5. **Off-repo checklist** (recommendations, not code):
   - Google Search Console: verify property, submit sitemap.
   - Yandex Webmaster likewise (RU audience).
   - Consistent VPN phrasing in future release notes.
   - Community guide post on r/SteamDeck; submissions to awesome-decky /
     awesome-steam-deck lists (backlinks).
   - Decky Store listing text refresh after plugin.json change ships.

## Success criteria

- Repo appears in GitHub search for `steam deck vpn` (days after reindex).
- All locale pages build with valid hreflang/canonical/sitemap; Lighthouse
  SEO score ≥ 95.
- Google indexes new titles ("VPN & Proxy Client for Steam Deck") — tracked
  via Search Console after the maintainer connects it.
- Realistic expectation: outranking the Amnezia discussion (5k+ star repo
  authority) is a long game; outranking `hiddify-steam-deck-vpn` (25 stars)
  is achievable on merit signals.

## Non-goals

- Repo rename.
- Translating dev docs (`docs/DEVELOPMENT.md`, `docs/RELEASING.md`).
- Any keyword stuffing beyond the honest hybrid positioning.

## Risks

- Pages cutover: brief window where the site serves stale content while the
  first workflow deploy runs. Mitigation: land the workflow + `site/` in one
  PR, flip the Pages source immediately after merge.
- URL stability: current site is single-page (`/xray-decky/` +
  `changelog.html`). Astro must preserve `/xray-decky/changelog.html` (or
  ship a redirect) so existing links don't 404.
- RTL (`/fa/`): needs `dir="rtl"` handling in the ported CSS; scoped, but
  must be visually checked.
