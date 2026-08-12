import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://vadimonix.github.io',
  base: '/xray-decky',
  // 'preserve' keeps each page's own extension/nesting: index.astro -> index.html,
  // changelog.astro -> changelog.html, and (once added) ru/index.astro -> ru/index.html.
  // 'file' would flatten a future locale index to ru.html, 404ing the planned /ru/ URLs.
  build: { format: 'preserve' },
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
