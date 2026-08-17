#!/usr/bin/env node
/**
 * SEO invariant checks. Two modes:
 *
 *   node scripts/seo-check.mjs --readme   # README×5 parity (no build needed)
 *   node scripts/seo-check.mjs --site     # built site in site/dist
 *
 * Zero dependencies — plain string/regex checks over committed files and build
 * output. The rules being enforced are documented in AGENTS.md ("SEO surfaces")
 * and .claude/skills/seo-surfaces/; when a check fires, fix the content, don't
 * delete the check.
 */
import { readFileSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => readFileSync(resolve(ROOT, p), 'utf8');

let failures = 0;
const fail = (msg) => {
  failures++;
  console.error(`FAIL ${msg}`);
};
const ok = (msg) => console.log(`ok   ${msg}`);

/** The single source of truth for donation addresses. */
function donationAddresses() {
  const src = read('site/src/lib/donations.ts');
  const addrs = [...src.matchAll(/address: '([^']+)'/g)].map((m) => m[1]);
  if (addrs.length === 0) fail('donations.ts: no addresses parsed — regex or file moved?');
  return [...new Set(addrs)];
}

const READMES = ['README.md', 'README.ru.md', 'README.zh-CN.md', 'README.fa.md', 'README.es.md'];
const BANNER = 'site/public/assets/hero-banner-800w.png';

function checkReadmes() {
  const addrs = donationAddresses();
  const sectionCounts = {};

  for (const file of READMES) {
    if (!existsSync(resolve(ROOT, file))) {
      fail(`${file}: missing`);
      continue;
    }
    const s = read(file);
    const lines = s.split('\n');

    if (!/^# .*Steam Deck/.test(lines[0])) fail(`${file}: H1 must contain "Steam Deck"`);
    if (!/VPN/i.test(lines[0])) fail(`${file}: H1 must contain "VPN"`);

    // Language switcher row: 5 entries — 4 links to sibling READMEs + bold self.
    const switcher = lines[2] ?? '';
    const links = READMES.filter((r) => r !== file && switcher.includes(`(${r})`));
    if (links.length !== 4) fail(`${file}: switcher row (line 3) must link the other 4 READMEs, found ${links.length}`);
    if (!/\*\*[^*]+\*\*/.test(switcher)) fail(`${file}: switcher row must bold the current language`);

    if (!s.includes(`(${BANNER})`)) fail(`${file}: hero banner image missing`);

    sectionCounts[file] = (s.match(/^## /gm) ?? []).length;

    const missing = addrs.filter((a) => !s.includes(a));
    if (missing.length) fail(`${file}: donation addresses missing or drifted: ${missing.join(', ')}`);
  }

  const counts = Object.values(sectionCounts);
  if (new Set(counts).size > 1) {
    fail(`README section counts diverged: ${JSON.stringify(sectionCounts)} — translations out of sync`);
  } else if (counts.length === READMES.length) {
    ok(`README×5 in sync: ${counts[0]} sections each, switcher/banner/addresses present`);
  }
  if (!existsSync(resolve(ROOT, BANNER))) fail(`${BANNER}: banner file missing`);
}

const DIST = 'site/dist';
const LANDINGS = ['index.html', 'ru/index.html', 'zh/index.html', 'fa/index.html', 'es/index.html'];
const GUIDES = [
  'vpn-on-steam-deck.html',
  'ru/vpn-on-steam-deck.html',
  'zh/vpn-on-steam-deck.html',
  'fa/vpn-on-steam-deck.html',
  'es/vpn-on-steam-deck.html',
];
const PAGES = [...LANDINGS, ...GUIDES, 'changelog.html'];

function checkSite() {
  if (!existsSync(resolve(ROOT, DIST, 'index.html'))) {
    fail(`${DIST}: not built — run \`pnpm build\` in site/ first`);
    return;
  }
  const version = JSON.parse(read('package.json')).version;
  const addrs = donationAddresses();
  const canonicals = new Set();
  /** canonical URL -> "hreflang=href" pairs declared in that page's <head>. */
  const pageAlternates = new Map();

  for (const page of PAGES) {
    const path = `${DIST}/${page}`;
    if (!existsSync(resolve(ROOT, path))) {
      fail(`${path}: missing from build`);
      continue;
    }
    const s = read(path);

    const title = s.match(/<title>([^<]*)<\/title>/)?.[1] ?? '';
    if (!title.includes('Xray Decky')) fail(`${page}: <title> must contain "Xray Decky", got "${title}"`);
    if (!/<meta name="description" content="[^"]+"/.test(s)) fail(`${page}: meta description missing/empty`);

    const canonical = s.match(/<link rel="canonical" href="([^"]+)"/)?.[1];
    if (!canonical) fail(`${page}: canonical missing`);
    else canonicals.add(canonical);

    const alternates = [...s.matchAll(/<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"/g)];
    if (canonical) pageAlternates.set(canonical, alternates.map((m) => `${m[1]}=${m[2]}`).sort());

    const hreflangs = (s.match(/hreflang=/g) ?? []).length;
    const expected = page === 'changelog.html' ? 0 : 6;
    if (hreflangs !== expected) fail(`${page}: expected ${expected} hreflang links, found ${hreflangs}`);

    if ((page.startsWith('fa/') ? 1 : 0) !== (s.includes('dir="rtl"') ? 1 : 0)) {
      fail(`${page}: dir="rtl" ${page.startsWith('fa/') ? 'missing' : 'unexpected'}`);
    }
  }

  for (const page of LANDINGS) {
    const s = read(`${DIST}/${page}`);
    const title = s.match(/<title>([^<]*)<\/title>/)?.[1] ?? '';
    if (!title.includes('VPN')) fail(`${page}: landing <title> must contain "VPN"`);

    const blocks = [...s.matchAll(/<script type="application\/ld\+json">(.*?)<\/script>/gs)].map((m) => m[1]);
    if (blocks.length !== 2) {
      fail(`${page}: expected 2 JSON-LD blocks, found ${blocks.length}`);
      continue;
    }
    try {
      const app = JSON.parse(blocks[0]);
      const faq = JSON.parse(blocks[1]);
      if (app['@type'] !== 'SoftwareApplication') fail(`${page}: JSON-LD block 1 is not SoftwareApplication`);
      if (app.softwareVersion !== version) {
        fail(`${page}: JSON-LD softwareVersion "${app.softwareVersion}" != package.json "${version}"`);
      }
      if (faq['@type'] !== 'FAQPage' || (faq.mainEntity ?? []).length < 8) {
        fail(`${page}: FAQPage JSON-LD missing or has <8 questions`);
      }
    } catch {
      fail(`${page}: JSON-LD does not parse`);
    }

    const missing = addrs.filter((a) => !s.includes(a));
    if (missing.length) fail(`${page}: donation addresses missing: ${missing.join(', ')}`);
  }

  const index = read(`${DIST}/index.html`);
  if (!index.includes('google-site-verification')) fail('index.html: Search Console verification tag stripped');
  if (!index.includes('yandex-verification')) fail('index.html: Yandex verification tag stripped');

  const robots = existsSync(resolve(ROOT, `${DIST}/robots.txt`)) ? read(`${DIST}/robots.txt`) : '';
  if (!robots.includes('sitemap-index.xml')) fail('robots.txt: missing or does not reference sitemap-index.xml');

  // Search Console is pointed at the index, so the index must exist and name
  // the child sitemap by absolute URL — a relative <loc> there is unfetchable.
  const indexPath = `${DIST}/sitemap-index.xml`;
  if (!existsSync(resolve(ROOT, indexPath))) {
    fail(`${indexPath}: missing — Search Console submission points at it`);
  } else {
    const children = [...read(indexPath).matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]);
    if (!children.includes('https://vadimonix.github.io/xray-decky/sitemap-0.xml')) {
      fail(`sitemap-index.xml: does not list the absolute sitemap-0.xml URL, got ${JSON.stringify(children)}`);
    }
  }

  const sitemapPath = `${DIST}/sitemap-0.xml`;
  if (!existsSync(resolve(ROOT, sitemapPath))) {
    fail(`${sitemapPath}: missing`);
  } else {
    const xml = read(sitemapPath);
    const entries = [...xml.matchAll(/<url>(.*?)<\/url>/gs)].map((m) => m[1]);
    const sitemapSet = new Set();
    for (const entry of entries) {
      const loc = entry.match(/<loc>([^<]+)<\/loc>/)?.[1];
      if (!loc) {
        fail('sitemap: <url> entry without <loc>');
        continue;
      }
      sitemapSet.add(loc);
      // Google requires the hreflang annotations to agree across delivery
      // methods; a set that differs from the page's own <link rel="alternate">
      // (historically: no x-default in the sitemap) makes it discard them.
      const alts = [...entry.matchAll(/<xhtml:link rel="alternate" hreflang="([^"]+)" href="([^"]+)"\/>/g)]
        .map((m) => `${m[1]}=${m[2]}`)
        .sort();
      const pageAlts = pageAlternates.get(loc);
      if (pageAlts && JSON.stringify(alts) !== JSON.stringify(pageAlts)) {
        fail(`sitemap: hreflang alternates for ${loc} differ from the page's <head>\n  sitemap: ${alts.join(' ')}\n  page:    ${pageAlts.join(' ')}`);
      }
    }
    for (const c of canonicals) if (!sitemapSet.has(c)) fail(`sitemap: canonical not listed: ${c}`);
    for (const l of sitemapSet) if (!canonicals.has(l)) fail(`sitemap: URL has no page with that canonical: ${l}`);
    if (failures === 0) {
      ok(`site: ${PAGES.length} pages, canonicals == sitemap (${sitemapSet.size} URLs), hreflang sets match, JSON-LD v${version}`);
    }
  }
}

const mode = process.argv[2];
if (mode === '--readme') checkReadmes();
else if (mode === '--site') checkSite();
else {
  console.error('usage: seo-check.mjs --readme | --site');
  process.exit(2);
}

if (failures) {
  console.error(`\n${failures} SEO check(s) failed. Rules: AGENTS.md → "SEO surfaces".`);
  process.exit(1);
}
console.log('All SEO checks passed.');
