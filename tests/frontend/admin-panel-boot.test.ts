// @vitest-environment node
import { readFileSync } from 'node:fs';

import { JSDOM } from 'jsdom';
import { afterEach, describe, expect, it, vi } from 'vitest';

/**
 * Boot the real admin panel (admin.html + admin.js) in jsdom.
 *
 * The panel ships unbundled, so nothing else in the toolchain ever executes it;
 * this is the only place a broken top-level statement, a bad element reference
 * or a regression in the pairing flow surfaces before a device install.
 */

const read = (name: string) =>
  readFileSync(new URL(`../../defaults/static/${name}`, import.meta.url), 'utf8');

const adminHtml = read('admin.html');
const adminJs = read('admin.js');

interface Booted {
  dom: JSDOM;
  doc: Document;
  fetchMock: ReturnType<typeof vi.fn>;
  el: (id: string) => HTMLElement;
}

/** Let the panel's promise chains settle (it polls as soon as it has a token). */
const flush = async () => {
  for (let i = 0; i < 10; i++) await Promise.resolve();
};

interface ApiReply {
  status: number;
  body: unknown;
}

/**
 * Load the panel at `search` (e.g. '?token=abc'). Scripts are evaluated by hand
 * rather than via a <script src>, so jsdom never reaches for the network — the
 * stylesheet and favicon references in admin.html stay inert.
 */
function boot(
  search = '',
  language = 'en-US',
  reply: ApiReply = { status: 200, body: { success: true } }
): Booted {
  const dom = new JSDOM(adminHtml, {
    url: `https://192.168.1.5:8765/admin${search}`,
    runScripts: 'outside-only',
    pretendToBeVisual: true,
  });
  const { window } = dom;

  Object.defineProperty(window.navigator, 'language', { value: language, configurable: true });

  const fetchMock = vi.fn(async () => ({
    status: reply.status,
    json: async () => reply.body,
  }));
  // The panel starts polling as soon as it holds a token.
  (window as unknown as { fetch: unknown }).fetch = fetchMock;

  window.eval(adminJs);

  return {
    dom,
    doc: window.document,
    fetchMock,
    el: (id: string) => {
      const node = window.document.getElementById(id);
      if (!node) throw new Error(`#${id} missing from admin.html`);
      return node;
    },
  };
}

let booted: Booted | null = null;

afterEach(() => {
  booted?.dom.window.close();
  booted = null;
});

describe('boot without a token', () => {
  it('shows the pairing screen and hides the panel', () => {
    booted = boot();

    expect(booted.el('locked').hidden).toBe(false);
    expect(booted.el('panel').hidden).toBe(true);
    // No message means "not yet paired" rather than "that token was wrong".
    expect(booted.el('token-error').hidden).toBe(true);
  });

  it('makes no API calls before it is paired', () => {
    booted = boot();
    expect(booted.fetchMock).not.toHaveBeenCalled();
  });

  it('applies static translations to the markup', () => {
    booted = boot();

    const labelled = booted.doc.querySelectorAll('[data-i18n]');
    expect(labelled.length).toBeGreaterThan(20);
    for (const node of labelled) {
      // An unresolved key renders as the dotted key itself.
      expect(
        node.textContent?.trim(),
        `key ${node.getAttribute('data-i18n')} did not resolve`
      ).not.toMatch(/^[a-z]+(\.[a-zA-Z]+)+$/);
    }
    expect(booted.doc.documentElement.lang).toBe('en');
  });

  it('resolves placeholder and aria translations too', () => {
    booted = boot();

    for (const node of booted.doc.querySelectorAll('[data-i18n-ph]')) {
      expect(node.getAttribute('placeholder')).toBeTruthy();
      expect(node.getAttribute('placeholder')).not.toBe(node.getAttribute('data-i18n-ph'));
    }
    for (const node of booted.doc.querySelectorAll('[data-i18n-aria]')) {
      expect(node.getAttribute('aria-label')).toBeTruthy();
      expect(node.getAttribute('aria-label')).not.toBe(node.getAttribute('data-i18n-aria'));
    }
  });

  it('renders the Russian panel for a ru locale', () => {
    booted = boot('', 'ru-RU');
    expect(booted.doc.documentElement.lang).toBe('ru');
    expect(booted.el('lang-toggle').textContent).toBe('RU');
  });
});

describe('pairing via the QR token', () => {
  it('stores the token and strips it from the address bar', () => {
    booted = boot('?token=s3cret-token');
    const { window } = booted.dom;

    expect(window.sessionStorage.getItem('xray-decky-admin-token')).toBe('s3cret-token');
    // The QR URL carries the token; leaving it in the URL would persist it in
    // history and in any Referer the page emits.
    expect(window.location.search).toBe('');
    expect(window.location.pathname).toBe('/admin');
  });

  it('polls the API with the token in the header', async () => {
    booted = boot('?token=s3cret-token');
    await flush();

    expect(booted.fetchMock).toHaveBeenCalled();
    expect(booted.fetchMock.mock.calls.map((call) => call[0])).toContain('/api/v1/status');

    const headers = booted.fetchMock.mock.calls.map(
      (call) => (call[1] as { headers: Record<string, string> })?.headers?.['X-Admin-Token']
    );
    expect(headers.every((value) => value === 's3cret-token')).toBe(true);
  });

  it('unlocks the panel once the first status call succeeds', async () => {
    booted = boot('?token=s3cret-token');
    await flush();

    expect(booted.el('locked').hidden).toBe(true);
    expect(booted.el('panel').hidden).toBe(false);
  });

  it('re-locks and drops the stored token when the API answers 401', async () => {
    // A token that the Deck has rotated (plugin reinstall) must not leave the
    // panel showing a stale connected view.
    booted = boot('?token=stale-token', 'en-US', { status: 401, body: { success: false } });
    await flush();

    expect(booted.el('locked').hidden).toBe(false);
    expect(booted.el('panel').hidden).toBe(true);
    expect(booted.el('token-error').hidden).toBe(false);
    expect(booted.el('token-error').textContent).toBeTruthy();
    expect(booted.dom.window.sessionStorage.getItem('xray-decky-admin-token')).toBeNull();
  });

  it('preserves other query parameters while removing the token', () => {
    booted = boot('?token=abc&keep=1');
    expect(booted.dom.window.location.search).toBe('?keep=1');
  });
});
