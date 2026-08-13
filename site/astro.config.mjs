import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// Non-default locales are directories (ru/index.html), so their sitemap URLs
// must be the trailing-slash form the pages themselves use as canonical —
// appending .html would point at ru.html, which does not exist (404).
const LOCALE_DIRS = new Set(['ru', 'zh', 'fa', 'es']);

export default defineConfig({
  site: 'https://vadimonix.github.io',
  base: '/xray-decky',
  // 'preserve' keeps each page's own extension/nesting: index.astro -> index.html,
  // changelog.astro -> changelog.html, and (once added) ru/index.astro -> ru/index.html.
  // 'file' would flatten a future locale index to ru.html, 404ing the planned /ru/ URLs.
  build: { format: 'preserve' },
  // Astro's default HTML compression collapses the whole document onto a single
  // line, which makes the per-tag <head> output (canonical, hreflang alternates,
  // OG tags, JSON-LD) unreadable/ungreppable for SEO audits. Gzip/Brotli over the
  // wire recovers virtually all of the size difference anyway.
  compressHTML: false,
  integrations: [
    sitemap({
      i18n: {
        defaultLocale: 'en',
        locales: { en: 'en', ru: 'ru', zh: 'zh-CN', fa: 'fa', es: 'es' },
      },
      // The sitemap derives extensionless URLs from routes (/changelog), but with
      // build.format 'preserve' the real files — and every page's canonical — end
      // in .html (locale roots: trailing slash). Rewrite both the <loc> and the
      // auto-generated hreflang alternates so every sitemap URL string-matches
      // the canonical/hreflang the page itself declares.
      serialize(item) {
        const fix = (u) => {
          const url = new URL(u);
          const last = url.pathname.split('/').pop();
          if (last && !last.includes('.')) {
            url.pathname += LOCALE_DIRS.has(last) ? '/' : '.html';
          }
          return url.toString();
        };
        item.url = fix(item.url);
        if (item.links) {
          item.links = item.links.map((link) => ({ ...link, url: fix(link.url) }));
        }
        return item;
      },
    }),
  ],
  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'ru', 'zh', 'fa', 'es'],
    routing: { prefixDefaultLocale: false },
  },
});
