import { localePrefixes, type Locale } from '../i18n/locales';

const base = import.meta.env.BASE_URL.replace(/\/$/, '');
// import.meta.env.SITE mirrors astro.config.mjs's `site` — falls back to the
// current literal only if that config value is ever unset.
const site = (import.meta.env.SITE ?? 'https://vadimonix.github.io').replace(/\/$/, '');

/** Prefix a site-relative path with the deploy base: withBase('styles/main.css') → '/xray-decky/styles/main.css' */
export const withBase = (p: string): string => `${base}/${p.replace(/^\//, '')}`;

/** Absolute URL for canonical/hreflang/OG: absoluteUrl('ru/') → 'https://vadimonix.github.io/xray-decky/ru/' */
export const absoluteUrl = (p: string): string => `${site}${withBase(p)}`;

/**
 * Locale-prefixed site link for hrefs baked into dictionary copy:
 * localeHref('ru', 'vpn-on-steam-deck.html') → '/xray-decky/ru/vpn-on-steam-deck.html'.
 * Ties dict cross-links to the localePrefixes single source of truth so a
 * translated dict can't silently keep another locale's URL.
 */
export const localeHref = (locale: Locale, p: string): string =>
  withBase(`${localePrefixes[locale]}${p.replace(/^\//, '')}`);
