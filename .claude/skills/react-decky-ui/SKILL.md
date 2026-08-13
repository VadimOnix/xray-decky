---
name: react-decky-ui
description: React patterns specific to this plugin's Quick Access Menu UI running inside the Steam client CEF — @decky/ui usage, centralized panel state, poll+event data flow, i18n, RPC error conventions, what is testable. Use when writing or reviewing code in src/ (components, hooks, services), adding UI state or backend calls, or deciding how to test frontend changes.
---

# React in the Steam Deck Quick Access Menu

Repo-specific patterns for `src/`. Generic React guidance (memoization, effects, composition) → use the `react-best-practices` and `composition-patterns` skills; platform basics (definePlugin, callable, events) → `decky-plugin-dev` skill.

## Runtime constraints

- React is **the Steam client's copy**, injected at runtime. No `react`/`react-dom` in dependencies — only pinned `@types/react`. Never import anything that assumes its own React instance (context providers from foreign libs, portals to document.body outside the panel).
- The panel lives in Steam's CEF overlay: no `localStorage` (persistence goes through backend `SettingsManager`), no arbitrary DOM globals, gamepad-first navigation.
- Use `@decky/ui` components (`PanelSection`, `PanelSectionRow`, `Field`, `Toggle`, `ButtonItem`, `ErrorBoundary`) — they carry Steam's focus/gamepad behavior. Plain `<div>`s are fine for layout/text only.
- Wrap the panel content in `ErrorBoundary` from `@decky/ui` (see `src/index.tsx`).

## State architecture (one hook owns the panel)

`hooks/usePluginPanelState.ts` is the single owner of panel state; `index.tsx` picks `SetupLayout` vs `ConfiguredLayout` from its `layout` field, components below receive state + action callbacks as props. Don't scatter backend calls across components — extend the hook.

Data flow combines:
- **Poll**: status refresh every 2s (`POLL_INTERVAL_MS`) — but only while the panel is visible; gate background work with `useQuickAccessVisible()` from `@decky/ui`.
- **Push**: backend events via `addEventListener('vless_config_updated', …)`; always `removeEventListener` in cleanup.

Local component state is only for transient UI (loading flags, inline error text, form inputs) — see `ConnectionToggle.tsx`, which keeps `loading`/`error` local but gets `status` and `onToggle` from above.

## Backend calls

- All `callable()` wrappers live in `src/services/api.ts` with explicit TS types for both args and result — components import functions, never `callable` itself. Keep types in sync with the Python return shape.
- RPC results follow `{ success: boolean, error?: string }` — backend never throws across the boundary. UI pattern: `setLoading(true)` → await → branch on `result.success` → `finally setLoading(false)`.
- Validate user input on the frontend first (`utils/validation.ts`) for instant feedback; the backend re-validates authoritatively.

## i18n

`utils/i18n.ts`: `t(key, params?)` is a **pure function** — language detected once from `navigator.language` (`ru*` → RU, else EN), no runtime toggle, so no re-render wiring needed. Missing key falls back EN → key itself. Add keys to both dictionaries; the vitest suite (`tests/frontend/i18n.test.ts`) checks dictionary consistency.

(The web admin panel in `defaults/static/` has its own runtime-switchable i18n — different rules, different files.)

## Testing

- `@decky/ui` components can't render outside Steam — **no component render tests**. Testable surface: pure logic extracted to `utils/` and `services/` (validation, i18n, URL parsing), covered by vitest in `tests/frontend/`.
- Design accordingly: keep logic in plain TS functions, keep components thin.
- Real UI verification happens on a Deck (`decky-deploy-debug` skill; CEF DevTools via `chrome://inspect`).
