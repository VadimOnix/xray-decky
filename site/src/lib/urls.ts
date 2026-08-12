const base = import.meta.env.BASE_URL.replace(/\/$/, '');

/** Prefix a site-relative path with the deploy base: withBase('styles/main.css') → '/xray-decky/styles/main.css' */
export const withBase = (p: string): string => `${base}/${p.replace(/^\//, '')}`;

/** Absolute URL for canonical/hreflang/OG: absoluteUrl('ru/') → 'https://vadimonix.github.io/xray-decky/ru/' */
export const absoluteUrl = (p: string): string => `https://vadimonix.github.io${withBase(p)}`;
