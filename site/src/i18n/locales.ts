/**
 * Locale prefixes and BCP 47 language codes shared by every page's <head>
 * (canonical link, hreflang alternates, og:locale) and by Base.astro's nav
 * (locale-prefixed home link). Single source of truth so a locale is only
 * ever added in one place — this used to be an inline
 * `locale === 'en' ? '' : ...` check duplicated wherever a locale-aware URL
 * was built.
 */

export const LOCALES = ['en', 'ru', 'zh', 'fa', 'es'] as const;

export type Locale = (typeof LOCALES)[number];

/**
 * Path prefix (relative to the site base) for each locale's URLs, e.g.
 * localePrefixes.ru + 'changelog.html' -> 'ru/changelog.html'.
 * EN alone is unprefixed because astro.config.mjs sets
 * `i18n.routing.prefixDefaultLocale: false`.
 */
export const localePrefixes: Record<Locale, string> = {
  en: '',
  ru: 'ru/',
  zh: 'zh/',
  fa: 'fa/',
  es: 'es/',
};

/**
 * BCP 47 language codes used for `hreflang` alternates and `og:locale`.
 * `zh` maps to `zh-CN` (Simplified Chinese) to match the sitemap i18n
 * config in astro.config.mjs.
 */
export const hreflangCodes: Record<Locale, string> = {
  en: 'en',
  ru: 'ru',
  zh: 'zh-CN',
  fa: 'fa',
  es: 'es',
};
