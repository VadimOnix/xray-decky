# Tasks: Xray Decky Plugin UI Refactor (Decky/SteamOS UX)

**Input**: Design documents from `/specs/003-refactor-decky-ux/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Not requested. Only manual verification steps from `quickstart.md` are included as checkpoints.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare codebase for the UI refactor work (structure, shared UI state patterns).

- [x] T001 Create feature-level UI state hook skeleton in `src/hooks/usePluginPanelState.ts` (new)
- [x] T002 [P] Add a small shared UI primitives module for consistent spacing/help icon in `src/components/ui/` (new folder)
- [x] T003 [P] Add shared types for UI model in `src/types/ui.ts` (new) aligned to `specs/003-refactor-decky-ux/data-model.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core building blocks that must exist before implementing any story.

- [x] T004 Implement centralized polling + refetch contract in `src/hooks/usePluginPanelState.ts` (single interval; avoid per-component intervals)
- [x] T005 Implement event-driven refresh in `src/hooks/usePluginPanelState.ts` using `addEventListener/removeEventListener` for `vless_config_updated`
- [x] T006 Define “layout state” derivation (setup vs configured) in `src/hooks/usePluginPanelState.ts` from `getVLESSConfig().exists`
- [x] T007 Add backend callable for reset config in `src/services/api.ts` (`reset_vless_config`) and TypeScript types for response
- [x] T008 Implement backend method `reset_vless_config` in `main.py` (or appropriate backend module) using SettingsManager and emitting `vless_config_updated`
- [x] T009 Enforce reset precondition in backend `reset_vless_config` (reject if connection is active) in `main.py` (or backend state module)
- [x] T010 Verify backend import does not overwrite valid config on invalid Save in `main.py` and/or `backend/src/config_parser.py` (align with contract note for `import_vless_config`)

**Checkpoint**: Foundation ready — UI can switch layouts based on config existence, and reset callable exists with correct gating.

---

## Phase 3: User Story 1 — First-time setup layout (Priority: P1) 🎯 MVP

**Goal**: Dedicated Setup layout with QR + LAN address + textarea + explicit Save, using SteamOS-styled components where possible.

**Independent Test**: With no saved config, plugin shows Setup layout; Save validates and persists config; UI transitions to Configured without reload.

- [x] T011 [US1] Create `SetupLayout` component in `src/components/layouts/SetupLayout.tsx` (new) using composition over inline blocks
- [x] T012 [P] [US1] Refactor `src/components/QRImportBlock.tsx` to be embeddable inside Setup layout (remove debug-only UI, keep QR custom styling if needed)
- [x] T013 [P] [US1] Refactor `src/components/ConfigImport.tsx` into a “Save VLESS” form component (textarea + Save) suitable for Setup layout and driven by props
- [x] T014 [US1] Wire Setup layout to `usePluginPanelState` in `src/index.tsx` (render Setup only when config does not exist)
- [x] T015 [US1] Implement validation/error presentation for Save in Setup layout (front-end validation + backend error mapping) in `src/components/layouts/SetupLayout.tsx`
- [x] T016 [US1] Add help `?` popups for Setup-specific help topics (QR/LAN address/VLESS input) in `src/components/layouts/SetupLayout.tsx`

**Checkpoint**: US1 done — follow `quickstart.md` section “1) Setup layout (no saved config)”.

---

## Phase 4: User Story 2 — Daily connect + status + options (Priority: P2)

**Goal**: Focused Configured layout: Connect, status bar, config summary card, TUN/Kill Switch toggles, Reset (disabled while connected).

**Independent Test**: With saved config, plugin shows Configured layout; connect/status updates; toggles present; reset returns to Setup and is disabled while connected.

- [x] T017 [US2] Create `ConfiguredLayout` component in `src/components/layouts/ConfiguredLayout.tsx` (new)
- [x] T018 [P] [US2] Create config summary card component in `src/components/ConfigSummaryCard.tsx` (new) consuming config summary from `usePluginPanelState`
- [x] T019 [P] [US2] Refactor `src/components/StatusDisplay.tsx` into a status bar component driven by props (remove its internal polling)
- [x] T020 [P] [US2] Refactor `src/components/ConnectionToggle.tsx` into a primary Connect button driven by props + callbacks (remove its internal polling)
- [x] T021 [P] [US2] Refactor `src/components/TUNModeToggle.tsx` to be driven by props (remove its internal polling; move About text out)
- [x] T022 [P] [US2] Refactor `src/components/KillSwitchToggle.tsx` to be driven by props (remove its internal polling; move About text out)
- [x] T023 [US2] Implement “Options block” container in `src/components/OptionsBlock.tsx` (new) hosting TUN + Kill Switch toggles in a compact layout
- [x] T024 [US2] Implement Reset configuration UI in `src/components/ResetConfigurationButton.tsx` (new) calling `reset_vless_config` and forcing return to Setup on success
- [x] T025 [US2] Disable Reset configuration in UI when connection is active (connected/connecting/blocked) in `src/components/ResetConfigurationButton.tsx`
- [x] T026 [US2] Wire Configured layout to `usePluginPanelState` in `src/index.tsx` (render Configured only when config exists)

**Checkpoint**: US2 done — follow `quickstart.md` sections “2) Configured layout” + “3) Reset gating”.

---

## Phase 5: User Story 3 — Contextual help instead of “About” blocks (Priority: P3)

**Goal**: Move additional “About” text into help popups under `?` icons and keep layouts compact.

**Independent Test**: No large About blocks are permanently visible; help can be opened/dismissed without losing state.

- [x] T027 [US3] Create reusable help icon + popup wrapper in `src/components/ui/HelpPopover.tsx` (new)
- [x] T028 [P] [US3] Replace inline “About TUN Mode” block with `HelpPopover` in `src/components/TUNModeToggle.tsx`
- [x] T029 [P] [US3] Replace inline “About Kill Switch” block with `HelpPopover` in `src/components/KillSwitchToggle.tsx`
- [x] T030 [US3] Add contextual help for Reset configuration and status meanings in `src/components/layouts/ConfiguredLayout.tsx`

**Checkpoint**: US3 done — follow `quickstart.md` section “4) Contextual help popups”.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup, performance, and UX consistency across stories.

- [x] T031 [P] Remove debug logs / debug UI blocks from `src/services/api.ts` and `src/components/QRImportBlock.tsx` (keep only essential logging)
- [x] T032 Ensure consistent spacing/typography by replacing inline styles with `@decky/ui`-friendly composition patterns across `src/components/layouts/*`
- [x] T033 Reduce backend call frequency (tune polling interval) in `src/hooks/usePluginPanelState.ts` and confirm perceived status latency ≤ ~2s
- [x] T034 Run full manual validation from `specs/003-refactor-decky-ux/quickstart.md` and capture any follow-up fixes in this phase _(recommended to re-run before store submission)_
- [x] T035 Remove all per-component `setInterval` polling from `src/components/{StatusDisplay,ConnectionToggle,TUNModeToggle,KillSwitchToggle}.tsx` and ensure only `src/hooks/usePluginPanelState.ts` performs polling

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Setup completion; **blocks** all stories
- **US1 (P1)**: depends on Foundational; delivers MVP
- **US2 (P2)**: depends on Foundational; can proceed after US1 (recommended) to reuse layout/state patterns
- **US3 (P3)**: depends on US2 component refactors (About text removal)
- **Polish**: after US1–US3 (as desired)

### User Story Dependencies

- **US1**: foundational API/state in place
- **US2**: best after US1 (because it shares `usePluginPanelState` + layout selection)
- **US3**: best after US2 (help popovers replace About blocks in toggles)

---

## Parallel Opportunities

- Phase 1: `T002` and `T003` can run in parallel.
- Phase 3 (US1): `T011` and `T012` can run in parallel.
- Phase 4 (US2): `T017`–`T021` can run in parallel (separate files).
- Phase 5 (US3): `T027` and `T028` can run in parallel.

---

## Parallel Example: User Story 2

```bash
Task: "Refactor StatusDisplay.tsx into prop-driven component"
Task: "Refactor ConnectionToggle.tsx into prop-driven component"
Task: "Refactor TUNModeToggle.tsx into prop-driven component"
Task: "Refactor KillSwitchToggle.tsx into prop-driven component"
```

---

## Implementation Strategy

### MVP First (US1)

1. Phase 1–2 (foundation + reset API)
2. Implement Setup layout (US1)
3. Validate via `quickstart.md` Setup section

### Incremental Delivery

1. Add Configured layout (US2) and reset gating
2. Add help popovers (US3)
3. Polish (remove debug, unify styling, tune polling)
