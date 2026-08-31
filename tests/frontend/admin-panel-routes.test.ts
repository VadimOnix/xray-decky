// @vitest-environment node
import { readFileSync } from 'node:fs';

import { JSDOM } from 'jsdom';
import { afterEach, describe, expect, it, vi } from 'vitest';

/**
 * End-to-end coverage for the Routing rules card on the admin panel.
 *
 * Boots the real admin.js in jsdom (no bundler ever runs these files in the
 * wild — this is the only place a broken wiring or wrong element id surfaces
 * before a device install). Mocks fetch so the panel can talk to the new
 * GET/PUT /api/v1/route-rules endpoints without a real server.
 */

const read = (name: string) =>
  readFileSync(new URL(`../../defaults/static/${name}`, import.meta.url), 'utf8');

const adminHtml = read('admin.html');
const adminJs = read('admin.js');

interface ApiReply {
  status: number;
  body: unknown;
}

/** Per-URL reply table. The first matching URL wins; default is the fallback. */
interface ApiPlan {
  default?: ApiReply;
  byUrl?: Record<string, ApiReply>;
}

function boot(search = '?token=tok', language = 'en-US', plan: ApiPlan = {}) {
  const dom = new JSDOM(adminHtml, {
    url: `https://192.168.1.5:8765/admin${search}`,
    runScripts: 'outside-only',
    pretendToBeVisual: true,
  });
  const { window } = dom;

  Object.defineProperty(window.navigator, 'language', {
    value: language,
    configurable: true,
  });

  const calls: { url: string; method: string; body?: unknown }[] = [];

  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    const method = (init && init.method) || 'GET';
    let body: unknown;
    if (init && init.body) {
      try {
        body = JSON.parse(init.body as string);
      } catch {
        body = init.body;
      }
    }
    calls.push({ url, method, body });

    const match =
      plan.byUrl && Object.entries(plan.byUrl).find(([prefix]) => url.startsWith(prefix));
    const reply = (match ? match[1] : plan.default) || {
      status: 200,
      body: { success: true },
    };
    return {
      status: reply.status,
      json: async () => reply.body,
    } as unknown as Response;
  });
  (window as unknown as { fetch: unknown }).fetch = fetchMock;

  window.eval(adminJs);
  return { dom, window, doc: window.document, fetchMock, calls };
}

const flush = async () => {
  for (let i = 0; i < 10; i++) await Promise.resolve();
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe('Routing rules card', () => {
  it('renders the card with title + empty hint when GET returns no rules', async () => {
    const { doc, calls } = boot('?token=tok', 'en-US', {
      default: { status: 200, body: { success: true, rules: [], presets: [] } },
    });
    await flush();

    const card =
      doc.getElementById('routes-card') || doc.querySelector('[aria-labelledby="routes-title"]');
    expect(card).not.toBeNull();
    expect(doc.getElementById('rules-empty')).not.toBeNull();
    expect(doc.getElementById('routes-add-btn')).not.toBeNull();
    expect(doc.getElementById('rule-dialog')).not.toBeNull();

    // The panel should have issued GET /api/v1/route-rules.
    const routeCall = calls.find((c) => c.url.includes('/route-rules'));
    expect(routeCall).toBeTruthy();
    expect(routeCall?.method).toBe('GET');
  });

  it('renders a row per rule and pre-fills the typeahead', async () => {
    const rules = [
      {
        id: 'r1',
        enabled: true,
        action: 'direct',
        match: { type: 'geosite', value: 'geosite:cn' },
      },
      {
        id: 'r2',
        enabled: false,
        action: 'reject',
        match: { type: 'ip', value: '1.2.3.0/24' },
      },
    ];
    const presets = [{ type: 'geosite', value: 'geosite:cn' }];
    const { doc } = boot('?token=tok', 'en-US', {
      default: { status: 200, body: { success: true, rules, presets } },
    });
    await flush();

    const items = doc.querySelectorAll('.rule-item');
    expect(items.length).toBe(2);
    const presetsList = doc.getElementById('rule-presets');
    expect(presetsList).not.toBeNull();
    expect(presetsList?.querySelectorAll('option').length).toBe(1);
  });

  it('translates the routing card and dynamic rule labels in Chinese', async () => {
    const rules = [
      {
        id: 'r1',
        enabled: true,
        action: 'direct',
        match: { type: 'geosite', value: 'geosite:steam@cn' },
      },
    ];
    const { doc } = boot('?token=tok', 'zh-CN', {
      default: { status: 200, body: { success: true, rules, presets: [] } },
    });
    await flush();

    expect(doc.querySelector('[data-i18n="routes.title"]')?.textContent).toBe('路由规则');
    expect(doc.getElementById('routes-add-btn')?.textContent).toBe('添加规则');
    expect(doc.querySelector('.rule-badge-type')?.textContent).toBe('域名集合');
    expect(doc.querySelector('.rule-badge-action')?.textContent).toBe('直连');
  });

  it('PUTs new rules when the dialog saves', async () => {
    const { doc, calls } = boot('?token=tok', 'en-US', {
      default: { status: 200, body: { success: true, rules: [], presets: [] } },
    });
    await flush();

    // Open dialog via the Add button
    const addBtn = doc.getElementById('routes-add-btn') as HTMLButtonElement | null;
    expect(addBtn).not.toBeNull();
    addBtn?.click();
    await flush();

    const type = doc.getElementById('rule-type') as HTMLSelectElement;
    const value = doc.getElementById('rule-value') as HTMLInputElement;
    const action = doc.getElementById('rule-action') as HTMLSelectElement;
    if (type) type.value = 'geosite';
    if (value) value.value = 'geosite:google';
    if (action) action.value = 'proxy';

    const form = doc.getElementById('rule-form') as HTMLFormElement | null;
    form?.dispatchEvent(
      new (doc.defaultView as typeof window).Event('submit', { cancelable: true })
    );
    await flush();

    const putCall = calls.find((c) => c.method === 'PUT' && c.url.includes('/route-rules'));
    expect(putCall).toBeTruthy();
    expect(putCall?.body).toBeTruthy();
  });

  it('PUT validation failure shows the server reason', async () => {
    const { doc } = boot('?token=tok', 'en-US', {
      default: { status: 200, body: { success: true, rules: [], presets: [] } },
    });
    await flush();
    const addBtn = doc.getElementById('routes-add-btn') as HTMLButtonElement | null;
    addBtn?.click();
    await flush();
    const value = doc.getElementById('rule-value') as HTMLInputElement;
    if (value) value.value = '10.0.0.999/8'; // invalid CIDR
    const form = doc.getElementById('rule-form') as HTMLFormElement | null;
    form?.dispatchEvent(
      new (doc.defaultView as typeof window).Event('submit', { cancelable: true })
    );
    await flush();
    // The validation happens locally before the PUT — but in this test path the
    // value '10.0.0.999/8' isn't validated client-side, so a PUT is sent. The
    // mock below answers with the server's VALIDATION_ERROR.

    // Override fetch to answer validation error
    (doc.defaultView as unknown as { fetch: unknown }).fetch = vi.fn(
      async () =>
        ({
          status: 400,
          json: async () => ({
            success: false,
            error: "ip value must be a CIDR or single address: '10.0.0.999/8'",
            errorCode: 'VALIDATION_ERROR',
          }),
        }) as unknown as Response
    );
    // Trigger save again now that the mock is updated
    form?.dispatchEvent(
      new (doc.defaultView as typeof window).Event('submit', { cancelable: true })
    );
    await flush();
    const errBox = doc.getElementById('rule-dialog-error');
    expect(errBox?.hidden).toBe(false);
  });
});
