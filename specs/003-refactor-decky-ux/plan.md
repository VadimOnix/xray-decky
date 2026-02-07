# Implementation Plan: Xray Decky Plugin UI Refactor (Decky/SteamOS UX)

**Branch**: `003-refactor-decky-ux` | **Date**: 2026-02-03 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/003-refactor-decky-ux/spec.md`

## Summary

Refactor plugin UI to match Decky/SteamOS UX patterns, using `@decky/ui` components where possible, and restructure the plugin panel into **two layouts**:

- **Setup layout** (no saved config): QR + LAN import address + textarea for VLESS link + explicit manual Save.
- **Configured layout** (config exists): primary Connect action + connection status bar + config summary card + TUN/Kill Switch toggles + Reset configuration (disabled while connected) that forces return to Setup.

Additionally: move long “About” text out of the main flow into contextual help popups (question-mark icon), so the panel stays compact and scroll-minimal.

## Technical Context

**Language/Version**: TypeScript/React (frontend), Python 3.x (backend)  
**Primary Dependencies**: `@decky/ui` (SteamOS-styled UI components), `@decky/api` (callables/events), `qrcode.react` (QR), existing backend modules for xray/TUN/kill-switch management  
**Storage**: Decky `SettingsManager` (existing keys for VLESS config + options; no new DB)  
**Testing**: Manual on real Steam Deck (Game Mode + Desktop Mode). Optional smoke checks via CEF debugging for UI.  
**Target Platform**: Steam Deck / SteamOS with Decky Loader  
**Project Type**: Decky plugin (frontend `src/`, backend `main.py` + `backend/src/`)  
**Performance Goals**: One-screen primary controls in configured state; minimal backend calls (centralize polling); status updates perceived within ~2s  
**Constraints**: Avoid root unless required; avoid duplicative polling in multiple components; keep UI consistent with SteamOS; QR can remain custom-styled if needed  
**Scale/Scope**: Single-user plugin panel; UI refactor + small API additions (reset config; optional events) only

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

- **I. Standardized Project Structure**: Yes — `src/` frontend with `index.tsx`, backend in `main.py` + `backend/src/`.
- **II. Mandatory Metadata Files**: Yes — plugin.json, package.json, LICENSE present in repo.
- **III. Frontend Development Standards**: **Partial violation (documented)** — codebase already uses the **new Decky API split** (`@decky/api` + `@decky/ui`) instead of `decky-frontend-lib` `ServerAPI`. This is consistent with Deckbrew migration guidance where DFL ServerAPI is removed and backend calls use the new API ([Deckbrew: new API migration](https://wiki.deckbrew.xyz/en/plugin-dev/new-api-migration)).
- **IV. Backend Development Patterns**: Yes — Plugin class pattern + SettingsManager already used in codebase.
- **V. Build & Distribution Requirements**: Yes — standard decky build pipeline (dist/index.js); no packaging changes required for UI-only refactor.
- **VI. Security First**: Yes — no new sensitive inputs; configuration validation remains; reset is gated by connection state.
- **VII. Semantic Versioning**: Yes — will bump version when implementation is delivered.
- **VIII. Real Device Testing**: Yes — test on Steam Deck in both UI states + connect/reset constraints.

**Violations**: III (Frontend API) — see Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/003-refactor-decky-ux/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── frontend-backend-ui.md
└── tasks.md              # created by /speckit.tasks
```

### Source Code (repository root)

```text
main.py
backend/
├── __init__.py
└── src/
    ├── __init__.py
    ├── xray_manager.py
    ├── tun_manager.py
    ├── kill_switch.py
    ├── system_proxy.py
    ├── connection_manager.py
    ├── config_parser.py
    ├── error_codes.py
    ├── import_server.py
    ├── cert_utils.py
    └── ...
src/
├── index.tsx
├── services/
│   └── api.ts
├── utils/
│   └── validation.ts
├── hooks/
│   └── usePluginPanelState.ts
├── types/
│   └── ui.ts
└── components/
    ├── layouts/
    │   ├── SetupLayout.tsx
    │   └── ConfiguredLayout.tsx
    ├── ui/
    │   ├── primitives.tsx
    │   └── HelpPopover.tsx
    ├── QRImportBlock.tsx
    ├── ConfigImport.tsx
    ├── ConfigSummaryCard.tsx
    ├── StatusDisplay.tsx
    ├── ConnectionToggle.tsx
    ├── TUNModeToggle.tsx
    ├── KillSwitchToggle.tsx
    ├── OptionsBlock.tsx
    └── ResetConfigurationButton.tsx
```

**Structure Decision**: Decky plugin with backend + frontend. UI refactor will mostly change `src/index.tsx` composition and rework/replace current UI blocks with `@decky/ui`-styled components and shared state hooks (per `/frontend-patterns`).

## Complexity Tracking

| Violation                                   | Why Needed                                                                                                             | Simpler Alternative Rejected Because                                                                                                                                                                                                                           |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **III** (new Decky API split; no ServerAPI) | Codebase already migrated; aligns with Deckbrew guidance that DFL ServerAPI is removed and calls move to `@decky/api`. | Keeping ServerAPI would diverge from current working code and re-introduce known communication issues; migration is recommended and supported by Decky Loader 3.0+ ([Deckbrew: new API migration](https://wiki.deckbrew.xyz/en/plugin-dev/new-api-migration)). |

## UX / UI Refactor Design (two-state layout)

### Layout selection logic

- Determine **UI layout state** from persisted config existence (`get_vless_config().exists`).
- While on the “Setup” layout, successful Save transitions to “Configured” immediately (no reload).
- “Reset configuration” clears config and forces return to “Setup”.

### State ownership (React best practices)

To reduce duplication and improve performance:

- Create a single “panel state” hook that owns:
  - config existence + config summary
  - connection status
  - option statuses (TUN, Kill Switch)
- Pass data down via props (composition) or a lightweight Context if needed.
- Avoid multiple components each polling the backend independently (current code polls in 3+ places). Centralize polling to one interval (or switch to event-driven updates where available).

### Contextual help popups

- Replace large “About …” blocks with a small help icon.
- On help activation, show a popup that does not consume permanent vertical space.
- Implementation decision: implement a reusable `HelpPopover` component that **always** works by using a Decky-provided transient primitive (toast/notification) as the baseline. If a stable `@decky/ui` modal/dialog primitive is confirmed during implementation, `HelpPopover` may switch to it without changing call sites.

## Phase 0: Research (output: research.md)

Resolve/confirm:

- Which `@decky/ui` components best map to the required layout primitives (sections/rows/buttons/toggles/cards).
- Most stable way to implement contextual help popups in Decky plugins with `@decky/api`/`@decky/ui`.
- Best practice for backend-call minimization: polling interval, event usage (`addEventListener` usage already present for config updates).

Primary references:

- Deckbrew “new API migration” (split into `@decky/api` and `@decky/ui`) ([link](https://wiki.deckbrew.xyz/en/plugin-dev/new-api-migration)).
- Decky plugin template (`@decky/ui` usage patterns) ([GitHub](https://github.com/SteamDeckHomebrew/decky-plugin-template)).

## Phase 1: Design & Contracts (output: data-model.md, contracts/\*, quickstart.md)

- **Data model**: define UI state model (layout state, config summary, connection status, option states) and transitions.
- **Contracts**: define frontend↔backend callable API needed for UI refactor:
  - Existing callables for status/toggles/config fetch remain.
  - Add callable to **reset/clear configuration**.
  - Clarify event semantics used to refresh UI after changes (e.g., existing `vless_config_updated`).
- **Quickstart**: developer steps to verify both layouts, reset gating, and help popups on a real Steam Deck.
