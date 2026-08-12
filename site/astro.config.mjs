import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

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
      // in .html. Re-append it so sitemap URLs string-match the canonicals.
      serialize(item) {
        const url = new URL(item.url);
        const last = url.pathname.split('/').pop();
        if (last && !last.includes('.')) {
          url.pathname += '.html';
          item.url = url.toString();
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
