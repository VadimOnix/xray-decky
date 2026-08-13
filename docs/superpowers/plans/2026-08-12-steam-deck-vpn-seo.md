# Steam Deck VPN SEO Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-extended-cc:subagent-driven-development (recommended) or superpowers-extended-cc:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the repo and its site rank for `steam deck vpn` (and related queries) by adopting hybrid "VPN & Proxy" positioning across repo metadata, README (5 languages), and a rebuilt multilingual GitHub Pages site.

**Architecture:** Repo metadata is patched live via `gh api`. The hand-written `docs/` site migrates to an Astro project in `site/` with locale routes `/`, `/ru/`, `/zh/`, `/fa/` (RTL), `/es/`, one shared markup component per page fed by per-locale dictionaries, full SEO head (hreflang, canonical, OG, JSON-LD), sitemap, and a GitHub Actions Pages deploy replacing the legacy `master:/docs` source.

**Tech Stack:** Astro ^5 + @astrojs/sitemap, pnpm 9, GitHub Actions (`actions/deploy-pages`), `gh` CLI.

**User decisions (already made):**
- Hybrid "VPN & Proxy client" positioning; repo NOT renamed.
- Scope = metadata + content (guide page, FAQ, structured data).
- Languages: EN (source of truth), RU, ZH (Simplified), FA, ES.
- Site i18n via a static-site generator (Astro chosen: matches pnpm ecosystem), not hand-maintained HTML copies.

**Spec:** `docs/superpowers/specs/2026-08-12-steam-deck-vpn-seo-design.md`

---

## File Structure

```
site/                              # NEW — Astro project (standalone, not a pnpm workspace member)
├── package.json                   # astro + @astrojs/sitemap only
├── astro.config.mjs               # site/base/i18n/sitemap config
├── public/
│   ├── robots.txt                 # NEW
│   ├── styles/main.css            # moved from docs/styles/main.css (+ RTL additions)
│   ├── scripts/demo.js            # moved from docs/scripts/demo.js
│   ├── scripts/changelog.js       # moved from docs/scripts/changelog.js
│   └── assets/…                   # moved from docs/assets/ (all images)
├── optimize-images.sh             # moved from docs/scripts/optimize-images.sh
└── src/
    ├── i18n/types.ts              # Dict type (landing + guide + seo strings)
    ├── i18n/{en,ru,zh,fa,es}.ts   # per-locale dictionaries; en.ts = copy extracted from docs/index.html
    ├── lib/urls.ts                # withBase() + absoluteUrl() helpers
    ├── layouts/Base.astro         # head: title/desc/canonical/hreflang/OG/JSON-LD slots, nav, footer
    ├── components/Landing.astro   # ported <main>+hero markup from docs/index.html, copy from dict
    ├── components/Guide.astro     # NEW guide page markup, copy from dict
    ├── components/LangSwitcher.astro
    ├── components/JsonLd.astro    # SoftwareApplication + FAQPage emitters
    └── pages/
        ├── index.astro            # <Landing t={en}>
        ├── changelog.astro        # ported docs/changelog.html (EN only)
        ├── vpn-on-steam-deck.astro        # <Guide t={en}>
        └── {ru,zh,fa,es}/
            ├── index.astro
            └── vpn-on-steam-deck.astro
.github/workflows/pages.yml        # NEW — build site/ → deploy-pages
README.md                          # rewritten H1/intro + language switcher row
README.{ru,zh-CN,fa,es}.md         # NEW translations
plugin.json                        # description gains VPN wording
package.json                       # description/keywords gain vpn, steam-deck
docs/index.html, docs/changelog.html, docs/styles/, docs/scripts/, docs/assets/   # DELETED (absorbed into site/)
```

URL invariants after migration (Astro `build.format: 'file'`):
- `https://vadimonix.github.io/xray-decky/` → dist/index.html (unchanged)
- `…/xray-decky/changelog.html` → dist/changelog.html (unchanged — no 404 for old links)
- New: `…/xray-decky/vpn-on-steam-deck.html`, `…/xray-decky/{ru,zh,fa,es}/index.html`, `…/xray-decky/{ru,zh,fa,es}/vpn-on-steam-deck.html`

---

### Task 1: Repo metadata, plugin.json, package.json

**Goal:** Inject "VPN" + spaced "Steam Deck" keywords into every metadata surface GitHub search indexes.

**Files:**
- Modify: `plugin.json` (publish.description)
- Modify: `package.json:4` (description) and `package.json:25-31` (keywords)
- Live (no file): repo description + topics via `gh api`

**Acceptance Criteria:**
- [ ] `gh repo view --json description` contains "VPN" and "Steam Deck" (two words)
- [ ] `gh repo view --json repositoryTopics` lists exactly 20 topics incl. `vpn`, `steam-deck-vpn`, `steamos-vpn`
- [ ] `plugin.json` publish.description starts with "VPN & proxy client for Steam Deck"
- [ ] `package.json` keywords include `vpn`, `steam-deck`, `steamos`

**Verify:** `gh repo view --json description,repositoryTopics` → shows new values; `git diff` shows only the two JSON files changed; `pnpm run lint:prettier` passes.

**Steps:**

- [ ] **Step 1: Patch live repo description**

```bash
gh api -X PATCH repos/VadimOnix/xray-decky \
  -f description='VPN & proxy client for Steam Deck — Decky Loader plugin. VLESS, VMess, Trojan, Shadowsocks, Hysteria2, TUIC · TUN mode for Gaming Mode · subscriptions · kill switch'
```

- [ ] **Step 2: Replace topics (exactly 20 = GitHub max)**

```bash
gh api -X PUT repos/VadimOnix/xray-decky/topics \
  -f 'names[]=decky-loader' -f 'names[]=decky-plugin' -f 'names[]=steamdeck' \
  -f 'names[]=vless' -f 'names[]=vless-reality' -f 'names[]=xray' \
  -f 'names[]=vpn' -f 'names[]=vpn-client' -f 'names[]=steam-deck' \
  -f 'names[]=steam-deck-vpn' -f 'names[]=steamos' -f 'names[]=steamos-vpn' \
  -f 'names[]=game-mode' -f 'names[]=sing-box' -f 'names[]=hysteria2' \
  -f 'names[]=tuic' -f 'names[]=shadowsocks' -f 'names[]=trojan' \
  -f 'names[]=v2ray' -f 'names[]=reality'
```

- [ ] **Step 3: Update plugin.json publish.description** (Decky Store listing; tags already contain `vpn`)

```json
"description": "VPN & proxy client for Steam Deck: VLESS (REALITY), VMess, Trojan, Shadowsocks, Hysteria2 and TUIC. TUN mode gives system-wide VPN coverage in Gaming Mode — subscriptions with a managed server list, kill switch, live traffic stats and a phone-friendly web admin panel."
```

- [ ] **Step 4: Update package.json**

```json
"description": "VPN & proxy client for Steam Deck — Decky Loader plugin for VLESS (Reality), VMess, Trojan, Shadowsocks, Hysteria2 and TUIC with TUN mode for Gaming Mode",
"keywords": ["decky", "plugin", "vless", "proxy", "xray", "vpn", "vpn-client", "steam-deck", "steamos", "sing-box"],
```

- [ ] **Step 5: Verify and commit**

```bash
gh repo view --json description,repositoryTopics
pnpm run lint:prettier
git add plugin.json package.json
git commit -m "feat(seo): VPN & Proxy positioning in repo metadata and store listing"
```

---

### Task 2: README (EN) rewrite

**Goal:** README H1 + intro carry "VPN", "Steam Deck" (spaced), "Gaming Mode" keywords with honest proxy-based-VPN framing; language switcher row added.

**Files:**
- Modify: `README.md:1-5` (H1 + intro), `README.md:30` (TUN feature line)

**Acceptance Criteria:**
- [ ] H1 is `Xray Decky — VPN & Proxy Client for Steam Deck`
- [ ] Language switcher row links to the four translation files (created in Task 3 — links may 404 until then, acceptable inside one PR)
- [ ] Intro paragraph contains phrases "VPN on your Steam Deck" and "Gaming Mode" verbatim
- [ ] No other sections lost; `grep -c '^## ' README.md` unchanged from before edit

**Verify:** `head -20 README.md` shows new H1/switcher/intro; `pnpm run lint:prettier` passes.

**Steps:**

- [ ] **Step 1: Replace lines 1–5 (H1 + intro) with:**

```markdown
# Xray Decky — VPN & Proxy Client for Steam Deck

**English** · [Русский](README.ru.md) · [中文](README.zh-CN.md) · [فارسی](README.fa.md) · [Español](README.es.md)

Run a VPN on your Steam Deck — including Gaming Mode. Xray Decky is a
[Decky Loader](https://wiki.deckbrew.xyz/) plugin: a full-featured
xray-core proxy client (VLESS/VMess/Trojan/Shadowsocks/Hysteria2/TUIC)
whose TUN mode routes **all** system traffic through an encrypted tunnel —
system-wide, VPN-style coverage where games can't ignore it. Multi-server
subscriptions, a Steam-styled web admin panel, kill switch and live
traffic stats included.
```

- [ ] **Step 2: Update the TUN feature bullet (line 30) to:**

```markdown
- **TUN Mode** — system-wide VPN-style routing through a virtual network
  interface, **recommended for Gaming Mode**.
```

- [ ] **Step 3: Verify and commit**

```bash
head -20 README.md
pnpm run lint:prettier
git add README.md
git commit -m "feat(seo): VPN & Proxy README positioning + language switcher"
```

---

### Task 3: README translations (RU, ZH, FA, ES)

**Goal:** Full translations of the Task-2 README as `README.ru.md`, `README.zh-CN.md`, `README.fa.md`, `README.es.md`.

**Files:**
- Create: `README.ru.md`, `README.zh-CN.md`, `README.fa.md`, `README.es.md`

**Acceptance Criteria:**
- [ ] Each file is a complete translation of README.md (all sections incl. Development)
- [ ] Each starts with the same language switcher row, current language unlinked/bold
- [ ] Code blocks, commands, file paths, protocol names, URLs stay untranslated
- [ ] All relative links point to the same targets as in README.md

**Verify:** `for f in README.ru.md README.zh-CN.md README.fa.md README.es.md; do grep -c '^## ' $f; done` → same section count as README.md; each file's first line is a localized H1 containing "Steam Deck" and local word for VPN client.

**Steps:**

- [ ] **Step 1: Translate README.md → README.ru.md.** H1: `# Xray Decky — VPN и прокси-клиент для Steam Deck`. Translate prose; keep code/links/technical terms verbatim.
- [ ] **Step 2: README.zh-CN.md.** H1: `# Xray Decky — Steam Deck 的 VPN 与代理客户端`
- [ ] **Step 3: README.fa.md.** H1: `# Xray Decky — کلاینت VPN و پروکسی برای Steam Deck` (RTL text renders fine in GitHub markdown; keep code blocks LTR as-is)
- [ ] **Step 4: README.es.md.** H1: `# Xray Decky — Cliente VPN y proxy para Steam Deck`
- [ ] **Step 5: Verify section parity and commit**

```bash
for f in README.md README.ru.md README.zh-CN.md README.fa.md README.es.md; do echo "$f: $(grep -c '^## ' $f)"; done
git add README.ru.md README.zh-CN.md README.fa.md README.es.md
git commit -m "docs: add RU/ZH/FA/ES README translations"
```

---

### Task 4: Astro scaffold + EN site port (visual parity)

**Goal:** `site/` Astro project builds the current landing + changelog pages pixel-identical at the same URLs, with copy extracted into an EN dictionary.

**Files:**
- Create: `site/package.json`, `site/astro.config.mjs`, `site/src/lib/urls.ts`, `site/src/i18n/types.ts`, `site/src/i18n/en.ts`, `site/src/layouts/Base.astro`, `site/src/components/Landing.astro`, `site/src/pages/index.astro`, `site/src/pages/changelog.astro`, `site/.gitignore`
- Move (git mv): `docs/styles/main.css` → `site/public/styles/main.css`; `docs/scripts/demo.js` → `site/public/scripts/demo.js`; `docs/scripts/changelog.js` → `site/public/scripts/changelog.js`; `docs/assets/*` → `site/public/assets/*`; `docs/scripts/optimize-images.sh` → `site/optimize-images.sh`
- Keep for now (deleted in Task 8): `docs/index.html`, `docs/changelog.html`

**Acceptance Criteria:**
- [ ] `cd site && pnpm install && pnpm build` succeeds
- [ ] `site/dist/index.html` and `site/dist/changelog.html` exist
- [ ] All copy in Landing.astro comes from `en.ts` dictionary (no hardcoded English prose in the component; markup-bearing strings rendered via `set:html`)
- [ ] Asset/script/style links resolve under base `/xray-decky/` from BOTH `/` and (future) `/ru/` pages — i.e. built via `withBase()`, never relative
- [ ] `astro preview` renders landing visually identical to https://vadimonix.github.io/xray-decky/ (nav, hero + animated demo, protocols, features, panel, install, usage, FAQ, footer)

**Verify:** `cd site && pnpm build && ls dist/index.html dist/changelog.html && grep -c 'xray-decky/styles/main.css' dist/index.html` → build OK, files exist, ≥1 match. Browser check via `pnpm preview`.

**Steps:**

- [ ] **Step 1: Scaffold config files**

`site/package.json`:
```json
{
  "name": "xray-decky-site",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "astro dev",
    "build": "astro build",
    "preview": "astro preview"
  },
  "devDependencies": {
    "astro": "^5.13.0",
    "@astrojs/sitemap": "^3.4.0"
  }
}
```

`site/astro.config.mjs`:
```js
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://vadimonix.github.io',
  base: '/xray-decky',
  build: { format: 'file' },
  integrations: [
    sitemap({
      i18n: {
        defaultLocale: 'en',
        locales: { en: 'en', ru: 'ru', zh: 'zh-CN', fa: 'fa', es: 'es' },
      },
    }),
  ],
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'ru', 'zh', 'fa', 'es'],
    routing: { prefixDefaultLocale: false },
  },
});
```

`site/.gitignore`:
```
node_modules/
dist/
.astro/
```

`site/src/lib/urls.ts`:
```ts
const base = import.meta.env.BASE_URL.replace(/\/$/, '');

/** Prefix a site-relative path with the deploy base: withBase('styles/main.css') → '/xray-decky/styles/main.css' */
export const withBase = (p: string): string => `${base}/${p.replace(/^\//, '')}`;

/** Absolute URL for canonical/hreflang/OG: absoluteUrl('ru/') → 'https://vadimonix.github.io/xray-decky/ru/' */
export const absoluteUrl = (p: string): string => `https://vadimonix.github.io${withBase(p)}`;
```

- [ ] **Step 2: Move static assets with git mv** (history preserved)

```bash
mkdir -p site/public/scripts
git mv docs/styles site/public/styles
git mv docs/assets site/public/assets
git mv docs/scripts/demo.js site/public/scripts/demo.js
git mv docs/scripts/changelog.js site/public/scripts/changelog.js
git mv docs/scripts/optimize-images.sh site/optimize-images.sh
rmdir docs/scripts
```

- [ ] **Step 3: Extract dictionary.** `site/src/i18n/types.ts` defines `Dict` covering every prose string of `docs/index.html` grouped by section (`seo`, `nav`, `hero`, `protocols`, `features[8]`, `panel`, `install`, `usage[3]`, `faq[]`, `footer`) plus `guide` (filled in Task 6). `site/src/i18n/en.ts` holds the strings copied **verbatim** from `docs/index.html` lines 6–9 (meta), 16–52 (nav+hero), 148 (caption), 154–353 (main). Strings containing inline markup (`<b>`, `<code>`, links) keep it and are rendered with `set:html`.

- [ ] **Step 4: Port markup.** `Base.astro` = html/head/nav/footer skeleton (head minimal in this task; SEO fills it in Task 5); `Landing.astro` = hero + main sections, markup copied from `docs/index.html` with prose replaced by `{t.…}` references; `pages/index.astro`:

```astro
---
import Base from '../layouts/Base.astro';
import Landing from '../components/Landing.astro';
import { en } from '../i18n/en';
---
<Base t={en} locale="en" path="">
  <Landing t={en} locale="en" />
</Base>
```

`pages/changelog.astro` ports `docs/changelog.html` body verbatim (EN-only page), loading `withBase('scripts/changelog.js')`.

- [ ] **Step 5: Build, compare, commit**

```bash
cd site && pnpm install && pnpm build
ls dist/index.html dist/changelog.html
grep -c '/xray-decky/styles/main.css' dist/index.html   # ≥1
pnpm preview   # visual side-by-side with production site
cd .. && git add site && git commit -m "feat(site): migrate GitHub Pages to Astro (EN parity port)"
```

---

### Task 5: SEO head — meta, hreflang, canonical, OG, JSON-LD, sitemap, robots

**Goal:** Every page emits a full SEO head; site ships sitemap + robots.txt.

**Files:**
- Modify: `site/src/layouts/Base.astro` (head)
- Create: `site/src/components/JsonLd.astro`, `site/public/robots.txt`
- Modify: `site/src/i18n/types.ts` + `en.ts` (`seo.title`, `seo.description` per page)

**Acceptance Criteria:**
- [ ] EN landing title: `Xray Decky — VPN & Proxy Client for Steam Deck` (localized per dict for other locales)
- [ ] Head contains: meta description, canonical, `og:*` (title/description/type/image/url/locale), `twitter:card`, and one `link rel="alternate" hreflang` per locale + `x-default` → EN (pages with `path === null`, e.g. changelog, skip alternates)
- [ ] Landing embeds JSON-LD `SoftwareApplication` (name, operatingSystem "SteamOS (Linux)", applicationCategory "UtilitiesApplication", offers price 0, url, softwareVersion from `plugin.json`-matching literal `2.2.0`, license MIT) and `FAQPage` generated from `t.faq`
- [ ] `pnpm build` emits `dist/sitemap-index.xml`; `robots.txt` points at it

**Verify:** `cd site && pnpm build && grep -c 'hreflang' dist/index.html` → 6 (5 locales + x-default); `grep -c 'application/ld+json' dist/index.html` → 2; `ls dist/sitemap-index.xml`.

**Steps:**

- [ ] **Step 1: Base.astro head** (props: `t`, `locale`, `path` — `path` is the locale-relative page path `''` | `'vpn-on-steam-deck.html'` | `null`):

```astro
---
import { withBase, absoluteUrl } from '../lib/urls';
const { t, locale, path = null } = Astro.props;
const locales = { en: '', ru: 'ru/', zh: 'zh/', fa: 'fa/', es: 'es/' };
const hreflangCodes = { en: 'en', ru: 'ru', zh: 'zh-CN', fa: 'fa', es: 'es' };
const canonical = absoluteUrl(`${locales[locale]}${path ?? ''}`);
---
<html lang={hreflangCodes[locale]} dir={locale === 'fa' ? 'rtl' : 'ltr'}>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{t.seo.title}</title>
  <meta name="description" content={t.seo.description} />
  <link rel="canonical" href={canonical} />
  {path !== null && Object.entries(locales).map(([loc, prefix]) => (
    <link rel="alternate" hreflang={hreflangCodes[loc]} href={absoluteUrl(`${prefix}${path}`)} />
  ))}
  {path !== null && <link rel="alternate" hreflang="x-default" href={absoluteUrl(path)} />}
  <meta property="og:title" content={t.seo.title} />
  <meta property="og:description" content={t.seo.description} />
  <meta property="og:type" content="website" />
  <meta property="og:url" content={canonical} />
  <meta property="og:image" content={absoluteUrl('assets/hero-banner-800w.png')} />
  <meta property="og:locale" content={hreflangCodes[locale]} />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="stylesheet" href={withBase('styles/main.css')} />
</head>
```

- [ ] **Step 2: JsonLd.astro** — emits two `<script type="application/ld+json">` blocks (SoftwareApplication + FAQPage from `t.faq` items as `Question`/`acceptedAnswer`); included by `Landing.astro` only.

- [ ] **Step 3: EN seo strings** in `en.ts`:

```ts
seo: {
  title: 'Xray Decky — VPN & Proxy Client for Steam Deck',
  description: 'Free open-source VPN & proxy client for Steam Deck (Decky Loader plugin). VLESS, VMess, Trojan, Shadowsocks, Hysteria2, TUIC — TUN mode for Gaming Mode, subscriptions, kill switch, web admin panel.',
},
```

- [ ] **Step 4: robots.txt**

```
User-agent: *
Allow: /

Sitemap: https://vadimonix.github.io/xray-decky/sitemap-index.xml
```

- [ ] **Step 5: Build, grep-verify, commit**

```bash
cd site && pnpm build
grep -c 'hreflang' dist/index.html          # 6
grep -c 'application/ld+json' dist/index.html  # 2
ls dist/sitemap-index.xml dist/robots.txt
cd .. && git add site && git commit -m "feat(site): full SEO head — hreflang, canonical, OG, JSON-LD, sitemap, robots"
```

---

### Task 6: Guide page (EN) + FAQ extension

**Goal:** Long-tail landing content: step-by-step "How to Set Up a VPN on Steam Deck" page + search-phrased FAQ entries on the landing.

**Files:**
- Create: `site/src/components/Guide.astro`, `site/src/pages/vpn-on-steam-deck.astro`
- Modify: `site/src/i18n/types.ts`, `site/src/i18n/en.ts` (guide strings + 3 new FAQ items), `site/src/layouts/Base.astro` (nav gains Guide link)

**Acceptance Criteria:**
- [ ] `dist/vpn-on-steam-deck.html` builds with its own title/description and hreflang set
- [ ] Guide covers: why VPN on Deck, prerequisites, 5 steps (Decky Loader → install plugin → import config → enable TUN → verify), troubleshooting links back to landing FAQ
- [ ] Landing FAQ gains: "Does the Steam Deck support a VPN?", "How do I use a VPN in Gaming Mode?", "Is Xray Decky a real VPN or a proxy?" — answers feed FAQPage JSON-LD automatically
- [ ] Nav shows Guide link on all pages

**Verify:** `cd site && pnpm build && grep -c 'hreflang' dist/vpn-on-steam-deck.html` → 6; `grep -c 'faq-item' dist/index.html` → 8 (5 old + 3 new).

**Steps:**

- [ ] **Step 1: Guide EN copy** (added to `en.ts` under `guide`; H1 and section copy below is the actual content, prose rendered from dict):

```
title: 'How to Set Up a VPN on Steam Deck (Gaming Mode Included)'
seoTitle: 'How to Set Up a VPN on Steam Deck — Gaming Mode Guide | Xray Decky'
seoDescription: 'Step-by-step guide: install a VPN on your Steam Deck with Decky Loader and Xray Decky — working in Gaming Mode via TUN, no desktop switching. VLESS, VMess, Trojan, Shadowsocks, Hysteria2, TUIC.'

intro: 'SteamOS has no built-in VPN client, and in Gaming Mode games ignore
system proxy settings entirely. This guide sets up Xray Decky — a free,
open-source VPN & proxy plugin for Decky Loader — so all your traffic is
tunneled system-wide, without ever leaving Gaming Mode.'

why (h2 "Why you need TUN, not just a proxy"): 'Steam ignores SOCKS proxy
settings in Gaming Mode. TUN mode creates a virtual network interface that
captures all system traffic — games, updates, voice chat — and routes it
through your encrypted server connection. That is what makes it behave like
a VPN rather than a browser-only proxy.'

prerequisites (h2): a Steam Deck (any model), Decky Loader installed, and a
server subscription or share link (vless://, vmess://, trojan://, ss://,
hysteria2://, tuic:// or a subscription URL).

steps (h2 "Five steps to a working VPN", ol):
1. Install Decky Loader — deckbrew.xyz wiki link (skip if installed).
2. Install Xray Decky — Quick Access (…) → Plugin Store → search "Xray Decky" → Install.
3. Import your server — open the plugin card in Quick Access, paste a share
   link or subscription URL; or scan the QR and paste it from your phone.
4. Enable TUN mode — one toggle in the plugin options; routes and cleanup
   are automatic. Optionally arm the kill switch for strict leak protection.
5. Connect and verify — flip the connection toggle, watch live speed in the
   card; open any geo-restricted store page or a what-is-my-ip site in the
   Deck browser to confirm the new exit IP.

troubleshooting (h2): link to landing #faq + note about recover.sh.
```

- [ ] **Step 2: Guide.astro + pages/vpn-on-steam-deck.astro** — same Base layout, `path="vpn-on-steam-deck.html"`, guide-specific `seo` overrides via props.

- [ ] **Step 3: Three FAQ additions to `en.ts` faq[]** (actual copy):

```
Q: 'Does the Steam Deck support a VPN?'
A: 'Not out of the box — SteamOS ships no VPN client and Gaming Mode ignores
system proxy settings. Xray Decky adds one as a Decky Loader plugin: its TUN
mode tunnels all system traffic, so it works in Gaming Mode too.'

Q: 'How do I use a VPN in Gaming Mode?'
A: 'Install the plugin, import a server link, enable TUN mode and connect —
all from the Quick Access menu, no desktop switching. See the step-by-step
guide: How to Set Up a VPN on Steam Deck.' (links to guide page)

Q: 'Is Xray Decky a real VPN or a proxy?'
A: 'Technically a proxy client (xray-core / sing-box) — but with TUN mode it
does what a VPN does: a virtual interface routes every packet from the
system through the encrypted tunnel. Without TUN it behaves as a SOCKS
proxy for Desktop Mode.'
```

- [ ] **Step 4: Nav link** in Base.astro nav list: `<a href={withBase('vpn-on-steam-deck.html')}>{t.nav.guide}</a>` (localized label; for non-EN locales points at `withBase(`${prefix}vpn-on-steam-deck.html`)`).

- [ ] **Step 5: Build, verify, commit**

```bash
cd site && pnpm build
grep -c 'hreflang' dist/vpn-on-steam-deck.html   # 6
grep -c 'faq-item' dist/index.html               # 8
cd .. && git add site && git commit -m "feat(site): VPN setup guide page + search-phrased FAQ entries"
```

---

### Task 7: Localized pages — RU, ZH, FA (RTL), ES

**Goal:** Landing + guide fully translated at `/ru/`, `/zh/`, `/fa/`, `/es/` with language switcher and RTL support.

**Files:**
- Create: `site/src/i18n/{ru,zh,fa,es}.ts`, `site/src/components/LangSwitcher.astro`, `site/src/pages/{ru,zh,fa,es}/index.astro`, `site/src/pages/{ru,zh,fa,es}/vpn-on-steam-deck.astro`
- Modify: `site/src/layouts/Base.astro` (mount switcher in nav), `site/public/styles/main.css` (append `[dir="rtl"]` block)

**Acceptance Criteria:**
- [ ] Full dictionary translations (every `Dict` key) for ru/zh/fa/es — TypeScript type-checks guarantee no missing keys
- [ ] `dist/{ru,zh,fa,es}/index.html` and `dist/{ru,zh,fa,es}/vpn-on-steam-deck.html` build
- [ ] `/fa/` pages render `dir="rtl"`, nav/hero/feature-grid mirror correctly (logical-property or `[dir="rtl"]` overrides for the handful of physical left/right rules in main.css)
- [ ] LangSwitcher on every localized page links the same page in all 5 locales
- [ ] Localized SEO titles, e.g. RU `Xray Decky — VPN и прокси-клиент для Steam Deck`, ZH `Xray Decky — Steam Deck 的 VPN 与代理客户端`, FA `Xray Decky — کلاینت VPN و پروکسی برای Steam Deck`, ES `Xray Decky — Cliente VPN y proxy para Steam Deck`
- [ ] Brand/technical tokens (Xray Decky, VLESS, REALITY, TUN, Decky Loader, protocol URIs) stay untranslated

**Verify:** `cd site && pnpm build && ls dist/ru/index.html dist/zh/index.html dist/fa/index.html dist/es/index.html dist/ru/vpn-on-steam-deck.html && grep -c 'dir="rtl"' dist/fa/index.html` → files exist, 1 match; `grep hreflang dist/ru/index.html | grep -c 'zh-CN'` → 1 (cross-locale alternates present).

**Steps:**

- [ ] **Step 1: Translate `en.ts` → `ru.ts`, `zh.ts`, `fa.ts`, `es.ts`** — full dictionaries typed `satisfies Dict`; inline markup (`<b>`, `<code>`, links) preserved inside translated strings.
- [ ] **Step 2: LangSwitcher.astro** — receives `locale` + `path`, renders 5 links (`EN Русский 中文 فارسی Español`), current locale marked `aria-current="page"`; mounted in Base nav.
- [ ] **Step 3: Locale pages** — thin wrappers, e.g. `pages/ru/index.astro`:

```astro
---
import Base from '../../layouts/Base.astro';
import Landing from '../../components/Landing.astro';
import { ru } from '../../i18n/ru';
---
<Base t={ru} locale="ru" path="">
  <Landing t={ru} locale="ru" />
</Base>
```

(same pattern ×8 for the four locales × landing/guide)

- [ ] **Step 4: RTL CSS** — audit `main.css` for physical `left/right/margin-left/...` rules affecting nav, hero, feature cards, install/usage lists; append a `[dir="rtl"]` override block at end of file (flip text-align, paddings, the nav flex order). Visual check `/fa/` in `pnpm preview`.
- [ ] **Step 5: Build, verify, commit**

```bash
cd site && pnpm build
ls dist/ru/index.html dist/zh/index.html dist/fa/index.html dist/es/index.html
grep -c 'dir="rtl"' dist/fa/index.html   # 1
cd .. && git add site && git commit -m "feat(site): RU/ZH/FA/ES locales with RTL support and language switcher"
```

---

### Task 8: Pages deploy workflow + legacy docs removal

**Goal:** CI builds `site/` and deploys to GitHub Pages; old hand-written site files removed.

**Files:**
- Create: `.github/workflows/pages.yml`
- Delete: `docs/index.html`, `docs/changelog.html`
- Modify: `README.md:88` (project-structure block: `docs/` line → `site/` line)

**Acceptance Criteria:**
- [ ] Workflow triggers on push to master touching `site/**` or `CHANGELOG.md`, plus `workflow_dispatch`
- [ ] Uses pnpm 9 / Node 22, `--frozen-lockfile`, uploads `site/dist` via `actions/upload-pages-artifact@v3`, deploys via `actions/deploy-pages@v4` with `pages: write` + `id-token: write` permissions and `github-pages` environment
- [ ] `docs/` retains only markdown docs + superpowers specs/plans (`git status` clean of strays)
- [ ] `site/pnpm-lock.yaml` committed (CI needs frozen lockfile)

**Verify:** `python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/pages.yml'))"` → no error; `ls docs/` → only .md files + subdirs `superpowers/`; `git ls-files site/pnpm-lock.yaml` → present.

**Steps:**

- [ ] **Step 1: Write `.github/workflows/pages.yml`:**

```yaml
name: Deploy GitHub Pages

on:
  push:
    branches: [master]
    paths: ['site/**', 'CHANGELOG.md', '.github/workflows/pages.yml']
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with:
          version: 9
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: pnpm
          cache-dependency-path: site/pnpm-lock.yaml
      - run: pnpm install --frozen-lockfile
        working-directory: site
      - run: pnpm build
        working-directory: site
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site/dist

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Delete legacy pages**

```bash
git rm docs/index.html docs/changelog.html
```

- [ ] **Step 3: Update README project-structure line** — replace `├── docs/                     # GitHub Pages (index.html, styles, assets)` with `├── site/                     # GitHub Pages site (Astro, 5 locales)`.

- [ ] **Step 4: Validate + commit**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/pages.yml'))"
ls docs/
git add -A && git commit -m "feat(ci): deploy Astro site to GitHub Pages via Actions; drop legacy docs site"
```

---

### Task 9: Final verification, PR, Pages cutover + off-repo checklist

**Goal:** Everything green, PR opened, cutover + off-repo actions documented and (where authorized) executed.

**Files:**
- None new (PR + live `gh` operations)

**Acceptance Criteria:**
- [ ] Repo-root `pnpm run lint`, `pnpm test`, `pytest tests/` all pass (site must not break plugin CI)
- [ ] `cd site && pnpm build` clean
- [ ] PR opened to master with summary + post-merge cutover checklist
- [ ] Pages source flipped to workflow AFTER merge (`gh api -X PUT repos/VadimOnix/xray-decky/pages -f build_type=workflow`), first deploy green, live site title contains "VPN & Proxy Client for Steam Deck"
- [ ] Off-repo checklist delivered to user (Search Console, Yandex Webmaster, sitemap submit, r/SteamDeck guide post, awesome-list submissions, release-notes phrasing)

**Verify:** `gh pr checks` green; after cutover `curl -s https://vadimonix.github.io/xray-decky/ | grep -o '<title>[^<]*'` → `<title>Xray Decky — VPN & Proxy Client for Steam Deck`; `curl -s https://vadimonix.github.io/xray-decky/ru/ | grep -c 'hreflang'` → 6.

**Steps:**

- [ ] **Step 1: Full test pass**

```bash
pnpm run lint && pnpm test && pytest tests/ && (cd site && pnpm build)
```

- [ ] **Step 2: Push branch + open PR** (needs user confirmation at checkpoint). PR body includes: what changed, URL invariants, post-merge cutover steps, off-repo checklist.
- [ ] **Step 3 (post-merge): flip Pages source + first deploy**

```bash
gh api -X PUT repos/VadimOnix/xray-decky/pages -f build_type=workflow
gh workflow run pages.yml
gh run watch
curl -s https://vadimonix.github.io/xray-decky/ | grep -o '<title>[^<]*</title>'
npx lighthouse https://vadimonix.github.io/xray-decky/ --only-categories=seo --chrome-flags='--headless' --output=json | python3 -c "import json,sys; print(json.load(sys.stdin)['categories']['seo']['score'])"   # ≥ 0.95 (spec criterion)
```

- [ ] **Step 4: Deliver off-repo checklist** (chat + PR body):
  1. Google Search Console: add property `vadimonix.github.io/xray-decky/` (URL-prefix), verify via HTML tag added to Base.astro if requested, submit `sitemap-index.xml`.
  2. Yandex Webmaster: same (RU traffic).
  3. r/SteamDeck: post the guide (link to `/vpn-on-steam-deck.html`).
  4. Submit repo to awesome-decky / awesome-steam-deck lists (backlinks).
  5. Future release notes: keep "VPN & proxy client for Steam Deck" phrasing.
  6. Decky Store re-submission picks up new plugin.json description on next release.

---

## Dependencies

- Task 3 ← Task 2
- Task 5 ← Task 4
- Task 6 ← Task 5
- Task 7 ← Task 6
- Task 8 ← Task 7
- Task 9 ← Tasks 1, 3, 8
