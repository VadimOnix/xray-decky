import { defineConfig } from 'vitest/config';

/**
 * Frontend test runner.
 *
 * Two things are under test here, neither of which the Python suite can reach:
 * `src/` (the QAM plugin, TypeScript) and `defaults/static/` (the web admin
 * panel — 1300 lines of no-build browser JS that ships to the device as-is).
 *
 * jsdom is the default environment because the admin-panel suite boots the real
 * admin.html + admin.js pair; the pure-logic suites are environment-agnostic.
 */
export default defineConfig({
  test: {
    include: ['tests/frontend/**/*.test.ts'],
    environment: 'jsdom',
    restoreMocks: true,
  },
});
