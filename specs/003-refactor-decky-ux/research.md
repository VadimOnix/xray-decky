# Research: Xray Decky Plugin UI Refactor (Decky/SteamOS UX)

**Branch**: `003-refactor-decky-ux`  
**Date**: 2026-02-03  
**Scope**: UI/UX refactor only (two-state layout + help popups + reset gating)

## Decisions

### 1) Use the new Decky API split (`@decky/api` + `@decky/ui`)

- **Decision**: Keep using `@decky/api` for backend calls/events and `@decky/ui` for SteamOS-styled UI components.
- **Rationale**: Deckbrew documents the split and removal of DFL ServerAPI; migration is recommended and the codebase already uses it successfully.
- **Source**: Deckbrew “Migrating to the new decky API” ([link](https://wiki.deckbrew.xyz/en/plugin-dev/new-api-migration)).
- **Alternatives considered**:
  - Reverting to `decky-frontend-lib` ServerAPI: rejected because it contradicts current working code and the documented migration path.

### 2) Two-state layout is driven by “config exists”

- **Decision**: The plugin panel renders exactly one of two layouts:
  - **Setup**: shown when `get_vless_config().exists` is false
  - **Configured**: shown when `get_vless_config().exists` is true
- **Rationale**: Matches spec requirements; aligns with typical onboarding vs daily-use separation and reduces clutter.
- **Alternatives considered**:
  - Single screen with many collapsible sections: rejected because it increases scrolling and weakens the primary CTA.

### 3) Centralize backend state polling and avoid per-component polling

- **Decision**: Replace multiple independent intervals (currently in `StatusDisplay`, `ConnectionToggle`, `KillSwitchToggle`, `TUNModeToggle`) with a single shared state hook at the panel level, following React best practices (composition, shared hooks).
- **Rationale**: Reduces duplicated backend calls, simplifies UI consistency, and lowers risk of out-of-sync UI.
- **Best-practice basis**: Use a single data-fetching hook pattern (like “query/refetch”) and pass state via props (composition) as recommended in `/frontend-patterns`.
- **Alternatives considered**:
  - Keep polling in each component: rejected because it’s wasteful and makes the UI harder to reason about.

### 4) Contextual help popups

- **Decision**: Replace long “About” blocks with a question-mark help affordance that opens a temporary popup.
- **Rationale**: Saves vertical space in Quick Access Menu.
- **Implementation strategy** (risk-managed):
  - Implement `HelpPopover` as a single reusable component that uses a stable Decky-provided transient primitive (toast/notification) as the baseline.
  - If a stable modal/dialog primitive from `@decky/ui` is confirmed during implementation, `HelpPopover` may be upgraded internally without changing call sites.
- **Alternatives considered**:
  - Keep About blocks inline: rejected (clutter, excessive scrolling).

### 5) Reset configuration contract + gating

- **Decision**: Add/standardize a backend callable to clear the saved configuration and emit an event so the UI can refresh immediately.
- **Rationale**: Spec requires Reset to force return to Setup and be disabled while connected; clearing must be atomic and reflected instantly.
- **Alternatives considered**:
  - Clearing only frontend state: rejected because config persistence is backend-owned (SettingsManager).

## Notes / Findings from current code

- Current UI is composed as a flat list in `src/index.tsx` and always renders all blocks, causing clutter.
- Multiple blocks poll backend on their own intervals (2–3 seconds), duplicating calls.
- “About …” content is currently inline in `TUNModeToggle` and `KillSwitchToggle` and must be moved into popups.

## References

- Deckbrew: new API migration (DFL → `@decky/api` + `@decky/ui`) — `https://wiki.deckbrew.xyz/en/plugin-dev/new-api-migration`
- Decky plugin template (example of `@decky/ui` usage) — `https://github.com/SteamDeckHomebrew/decky-plugin-template`
