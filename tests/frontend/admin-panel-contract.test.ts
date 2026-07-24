// @vitest-environment node
import { readFileSync } from 'node:fs';

import { describe, expect, it } from 'vitest';

/**
 * Source-level contracts for the shipped web admin panel.
 *
 * `defaults/static/` is no-build browser JS: it goes into the plugin zip exactly
 * as written, with no compiler or bundler to catch a renamed element id or a
 * translation key that only exists in one language. These checks stand in for
 * that missing step, and they are fast because they never boot a DOM.
 */

const read = (name: string) =>
  readFileSync(new URL(`../../defaults/static/${name}`, import.meta.url), 'utf8');

const adminJs = read('admin.js');
const adminHtml = read('admin.html');

const matchAll = (source: string, pattern: RegExp) =>
  [...source.matchAll(pattern)].map((m) => m[1]);

/** Keys defined in one of admin.js's two inline dictionaries. */
function dictionaryKeys(lang: 'en' | 'ru'): string[] {
  const start = adminJs.indexOf(`    ${lang}: {`);
  expect(start, `dictionary "${lang}" not found — did admin.js change shape?`).toBeGreaterThan(-1);
  const end = adminJs.indexOf('\n    },', start);
  const body = adminJs.slice(start, end);
  return matchAll(body, /^ {6}'([^']+)':/gm);
}

describe('element id contract', () => {
  it('resolves every getElementById lookup against admin.html', () => {
    const looked = matchAll(adminJs, /getElementById\('([^']+)'\)/g);
    const declared = new Set(matchAll(adminHtml, /\bid="([^"]+)"/g));

    expect(looked.length).toBeGreaterThan(40);
    // A missing id yields `els.foo === null`, and the first render that touches
    // it throws — leaving the panel stuck on a blank screen with no diagnostic.
    expect(looked.filter((id) => !declared.has(id))).toEqual([]);
  });

  it('declares no duplicate ids in admin.html', () => {
    const declared = matchAll(adminHtml, /\bid="([^"]+)"/g);
    const seen = new Set<string>();
    expect(declared.filter((id) => (seen.has(id) ? true : (seen.add(id), false)))).toEqual([]);
  });
});

describe('i18n contract', () => {
  it('backs every data-i18n attribute in admin.html with a key', () => {
    const used = new Set(matchAll(adminHtml, /\bdata-i18n(?:-ph|-aria)?="([^"]+)"/g));
    const en = new Set(dictionaryKeys('en'));

    expect(used.size).toBeGreaterThan(20);
    // applyStaticI18n() writes t(key) into the node; an unknown key renders the
    // raw dotted key to the user instead of a label.
    expect([...used].filter((key) => !en.has(key))).toEqual([]);
  });

  it('defines exactly the same keys in EN and RU', () => {
    const en = dictionaryKeys('en');
    const ru = dictionaryKeys('ru');

    expect(en.length).toBeGreaterThan(50);
    expect(new Set(en).size, 'duplicate keys in the EN dictionary').toBe(en.length);
    expect(new Set(ru).size, 'duplicate keys in the RU dictionary').toBe(ru.length);
    // t() falls back to EN for a missing key, so drift shows up as stray
    // English text in the Russian panel rather than as an error.
    expect(en.filter((key) => !ru.includes(key))).toEqual([]);
    expect(ru.filter((key) => !en.includes(key))).toEqual([]);
  });
});

describe('markup-injection contract', () => {
  it('never assigns markup from script', () => {
    // The panel renders strings it does not control: server names and
    // subscription titles arrive from whatever the subscription URL returns.
    // Every writer in admin.js uses textContent / createElement, and that is
    // the property keeping remote data out of the parser — so pin it.
    // Matched against code only; admin.js discusses the rule in a comment.
    const code = adminJs.replace(/\/\/[^\n]*/g, '').replace(/\/\*[\s\S]*?\*\//g, '');
    const sinks: [string, RegExp][] = [
      ['innerHTML', /\.innerHTML\s*=/],
      ['outerHTML', /\.outerHTML\s*=/],
      ['insertAdjacentHTML', /\.insertAdjacentHTML\s*\(/],
      ['document.write', /document\s*\.\s*write\s*\(/],
    ];
    for (const [name, pattern] of sinks) {
      expect(pattern.test(code), `admin.js must not use ${name}`).toBe(false);
    }
  });

  it('keeps the placeholder substitution non-expanding', () => {
    // String.replace would expand `$&` / `$'` in a value and rewrite only the
    // first placeholder; split/join does neither.
    expect(adminJs).toContain("str.split('{' + k + '}').join(String(params[k]))");
  });
});
