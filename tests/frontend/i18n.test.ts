// @vitest-environment node
import { readFileSync } from 'node:fs';

import { afterEach, describe, expect, it, vi } from 'vitest';

import { t } from '../../src/utils/i18n';

/**
 * Load a fresh copy of the module with a stubbed navigator language. The
 * detected language is captured in a module-level constant at import time, so
 * each locale needs its own module instance.
 */
async function importWithLocale(language: string) {
  vi.resetModules();
  vi.stubGlobal('navigator', { language });
  return import('../../src/utils/i18n');
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.resetModules();
});

describe('t', () => {
  it('returns the key itself when nothing is translated', () => {
    expect(t('definitely.not.a.key')).toBe('definitely.not.a.key');
  });

  it('interpolates named placeholders', () => {
    expect(t('tun.activeOn', { iface: 'xray0' })).toBe('Active on interface: xray0');
  });

  it('inserts values verbatim, without treating $ as a capture reference', () => {
    // Interpolated values include server names, which arrive from a remote
    // subscription — String.replace would expand `$&` / `$'` / `` $` `` here.
    expect(t('tun.activeOn', { iface: "$& $' $`" })).toBe("Active on interface: $& $' $`");
  });

  it('leaves placeholders alone when no params are supplied', () => {
    expect(t('tun.activeOn')).toContain('{iface}');
  });

  it('ignores params that the template does not mention', () => {
    expect(t('tun.activeOn', { nope: 'x' })).toBe('Active on interface: {iface}');
  });
});

describe('language detection', () => {
  it('selects Russian for any ru* locale', async () => {
    for (const locale of ['ru', 'ru-RU', 'RU-ru']) {
      const mod = await importWithLocale(locale);
      expect(mod.LANG).toBe('ru');
    }
  });

  it('falls back to English for every other locale', async () => {
    for (const locale of ['en-US', 'de', 'zh-CN', '']) {
      const mod = await importWithLocale(locale);
      expect(mod.LANG).toBe('en');
    }
  });

  it('translates through the Russian dictionary once ru is detected', async () => {
    const mod = await importWithLocale('ru-RU');
    expect(mod.t('status.connected')).toBe('Подключено');
  });
});

describe('source contracts', () => {
  const source = readFileSync(new URL('../../src/utils/i18n.ts', import.meta.url), 'utf8');

  it('substitutes every occurrence of a placeholder, not just the first', () => {
    // No shipped template repeats a placeholder today, so this is the only way
    // to pin the behaviour: String.replace with a string pattern rewrites one
    // occurrence, split/join rewrites all of them.
    expect(source).toContain('value.split(`{${name}}`).join(String(params[name]))');
  });

  // A key present in EN but missing from RU silently renders English text to a
  // Russian user — t()'s fallback hides the drift, so assert on it directly.
  // The dictionaries are module-private, so read them out of the source.
  it('defines exactly the same keys in both languages', () => {
    const keysOf = (name: string): string[] => {
      const start = source.indexOf(`const ${name}: Dict = {`);
      expect(start, `dictionary "${name}" not found — did i18n.ts change shape?`).toBeGreaterThan(
        -1
      );
      const body = source.slice(start, source.indexOf('\n};', start));
      return [...body.matchAll(/^ {2}'([^']+)':/gm)].map((m) => m[1]);
    };

    const en = keysOf('en');
    const ru = keysOf('ru');
    expect(en.length).toBeGreaterThan(50);
    expect(new Set(en).size, 'duplicate keys in the EN dictionary').toBe(en.length);
    expect(new Set(ru).size, 'duplicate keys in the RU dictionary').toBe(ru.length);
    expect(ru.filter((k) => !en.includes(k))).toEqual([]);
    expect(en.filter((k) => !ru.includes(k))).toEqual([]);
  });
});
