// @vitest-environment node
import { readFileSync } from 'node:fs';

import { JSDOM } from 'jsdom';
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
const adminCss = read('admin.css');

const matchAll = (source: string, pattern: RegExp) =>
  [...source.matchAll(pattern)].map((m) => m[1]);

/** Keys defined in one of admin.js's inline dictionaries. */
function dictionaryKeys(lang: 'en' | 'ru' | 'zh'): string[] {
  const start = adminJs.indexOf(`    ${lang}: {`);
  expect(start, `dictionary "${lang}" not found — did admin.js change shape?`).toBeGreaterThan(-1);
  const end = adminJs.indexOf('\n    },', start);
  const body = adminJs.slice(start, end);
  return matchAll(body, /^ {6}'([^']+)':/gm);
}

function dictionaryBody(lang: 'en' | 'ru' | 'zh'): string {
  const start = adminJs.indexOf(`    ${lang}: {`);
  expect(start, `dictionary "${lang}" not found — did admin.js change shape?`).toBeGreaterThan(-1);
  const end = adminJs.indexOf('\n    },', start);
  return adminJs.slice(start, end);
}

function dictionaryEntry(lang: 'en' | 'ru' | 'zh', key: string): string {
  const escaped = key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const body = dictionaryBody(lang);
  const start = body.search(new RegExp(`^ {6}'${escaped}':`, 'm'));
  expect(start, `dictionary entry "${key}" missing from ${lang}`).toBeGreaterThan(-1);
  const rest = body.slice(start);
  const next = rest.search(/\n {6}'[^']+':/);
  return next === -1 ? rest : rest.slice(0, next);
}

function placeholders(value: string): string[] {
  return [...value.matchAll(/\{([a-zA-Z][a-zA-Z0-9_]*)\}/g)].map((match) => match[1]).sort();
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

  it('defines exactly the same keys in EN, RU, and ZH', () => {
    const en = dictionaryKeys('en');
    const ru = dictionaryKeys('ru');
    const zh = dictionaryKeys('zh');

    expect(en.length).toBeGreaterThan(50);
    expect(new Set(en).size, 'duplicate keys in the EN dictionary').toBe(en.length);
    expect(new Set(ru).size, 'duplicate keys in the RU dictionary').toBe(ru.length);
    expect(new Set(zh).size, 'duplicate keys in the ZH dictionary').toBe(zh.length);
    // t() falls back to EN for a missing key, so drift shows up as stray
    // English text in the Russian panel rather than as an error.
    expect(en.filter((key) => !ru.includes(key))).toEqual([]);
    expect(ru.filter((key) => !en.includes(key))).toEqual([]);
    expect(en.filter((key) => !zh.includes(key))).toEqual([]);
    expect(zh.filter((key) => !en.includes(key))).toEqual([]);
  });
});

describe('static accessibility i18n contract', () => {
  it('routes the document title and every static aria-label through i18n', () => {
    const doc = new JSDOM(adminHtml).window.document;
    expect(doc.querySelector('title')?.getAttribute('data-i18n')).toBe('meta.title');

    const untranslated = [...doc.querySelectorAll('[aria-label]')].filter(
      (node) => !node.hasAttribute('data-i18n-aria')
    );
    expect(untranslated.map((node) => node.outerHTML)).toEqual([]);
  });

  it('localizes the initial loading and connection labels', () => {
    const doc = new JSDOM(adminHtml).window.document;
    const expected: [string, string][] = [
      ['#status-pill-text', 'st.unknown.t'],
      ['#hero-title', 'st.unknown.t'],
      ['#hero-sub', 'st.unknown.s'],
      ['#connect-btn-label', 'hero.connect'],
    ];

    for (const [selector, key] of expected) {
      expect(doc.querySelector(selector)?.getAttribute('data-i18n')).toBe(key);
    }
  });

  it('backs every literal translation lookup in admin.js with a dictionary key', () => {
    const used = new Set(matchAll(adminJs, /\bt\('([^']+)'\)/g));
    const en = new Set(dictionaryKeys('en'));
    expect([...used].filter((key) => !en.has(key))).toEqual([]);
  });

  it('keeps interpolation placeholders aligned across all locales', () => {
    for (const key of dictionaryKeys('en')) {
      const en = placeholders(dictionaryEntry('en', key));
      expect(
        placeholders(dictionaryEntry('ru', key)),
        `placeholder drift for ${key} in RU`
      ).toEqual(en);
      expect(
        placeholders(dictionaryEntry('zh', key)),
        `placeholder drift for ${key} in ZH`
      ).toEqual(en);
    }
  });
});

describe('routing row layout contract', () => {
  it('places the routing card on its own full-width grid row', () => {
    expect(adminHtml).toMatch(/<section class="card card-routes"/);
    expect(adminCss).toMatch(/\.card-routes\s*\{[\s\S]*?grid-column:\s*1\s*\/\s*-1/);
  });

  it('allows a narrow card to wrap the rule value and controls', () => {
    expect(adminCss).toMatch(/\.rule-item\s*\{[\s\S]*?flex-wrap:\s*wrap/);
    expect(adminCss).toMatch(/\.rule-value\s*\{[\s\S]*?flex-basis:\s*100%/);
    expect(adminCss).toMatch(
      /\.rule-item \.btn-small\s*\{[\s\S]*?max-width:\s*100%[\s\S]*?white-space:\s*normal/
    );
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
