const base = import.meta.env.BASE_URL.replace(/\/$/, '');
// import.meta.env.SITE mirrors astro.config.mjs's `site` — falls back to the
// current literal only if that config value is ever unset.
const site = (import.meta.env.SITE ?? 'https://vadimonix.github.io').replace(/\/$/, '');

/** Prefix a site-relative path with the deploy base: withBase('styles/main.css') → '/xray-decky/styles/main.css' */
export const withBase = (p: string): string => `${base}/${p.replace(/^\//, '')}`;

/** Absolute URL for canonical/hreflang/OG: absoluteUrl('ru/') → 'https://vadimonix.github.io/xray-decky/ru/' */
export const absoluteUrl = (p: string): string => `${site}${withBase(p)}`;
