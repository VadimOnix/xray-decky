# Tasks: Public Plugin Page with Steam Deck/SteamOS Styling

**Branch**: `004-plugin-public-page`  
**Input**: [spec.md](./spec.md), [plan.md](./plan.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently. No automated test tasks (not requested in spec).

**Format**: `- [ ] [ID] [P?] [Story?] Description with file path`

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Create folder structure and placeholder files for the static public page.

- [x] T001 Create directory structure: `docs/`, `docs/styles/`, `docs/assets/`, `docs/assets/features/` per plan.md
- [x] T002 [P] Add minimal `docs/index.html` with valid HTML5 document shell (doctype, html, head, body, charset, viewport)
- [x] T003 [P] Add minimal `docs/styles/main.css` with empty mobile-first base (e.g. box-sizing, root font-size)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Base semantic structure and Steam Deck–style theme so all user stories can build on it.

**Independent Test**: Open index.html in a browser; see a dark-themed page with header, main, and footer regions; resize to 375px and 1280px and confirm layout responds.

- [x] T004 Add semantic regions to `docs/index.html`: `<header>`, `<main>`, `<footer>`; ensure main contains placeholder sections for hero, features, install per contracts/README (page structure contract)
- [x] T005 Add Steam Deck–inspired CSS variables and base styles to `docs/styles/main.css`: dark background (e.g. #1b2838), surface/card (e.g. #2a475e), accent (e.g. #66c0f4), typography (system-ui or single webfont), mobile-first base layout
- [x] T006 Add responsive breakpoints to `docs/styles/main.css`: default for small viewport; `min-width` media queries for tablet (e.g. 768px) and desktop (e.g. 1280px) so layout and type scale

**Checkpoint**: Foundation ready—content (US1), visual refinement (US2), share/embed (US3), and media (US4) can proceed.

---

## Phase 3: User Story 1 – Discover and Understand the Plugin (Priority: P1) — MVP

**Goal**: Visitor sees plugin name, one-sentence purpose, platform (Steam Deck / Decky Loader), concise feature list, and how/where to install.

**Independent Test**: Open the page; without reading external docs, state the plugin name, what it does, and for which platform; see 4–6 features and an install path or link.

- [x] T007 [US1] Add plugin identity content to hero in `docs/index.html`: name (Xray Decky), one-sentence purpose, platform text (Steam Deck / Decky Loader), using data from plugin.json and README where applicable
- [x] T008 [US1] Add features section to `docs/index.html`: 4–6 primary features (e.g. import VLESS, toggle connection, TUN mode, kill switch) as list or card blocks with titles and short descriptions per data-model
- [x] T009 [US1] Add install section to `docs/index.html`: installation steps or a clear link to Plugin Store / README; ensure link is stable and has no user-specific paths (FR-002, FR-007)
- [x] T010 [US1] Ensure hero, features, and install content are readable and links are accessible at 375px and 1280px using existing `docs/styles/main.css` breakpoints

**Checkpoint**: User Story 1 is complete; a visitor can discover and understand the plugin and find install info.

---

## Phase 4: User Story 2 – Recognizable Steam Deck/SteamOS Visual Identity (Priority: P1)

**Goal**: Page looks and feels like Steam Deck/SteamOS: dark theme, accent colors, clear hierarchy, card/section style; layout and media scale across viewports.

**Independent Test**: Show the page to someone familiar with Steam Deck/SteamOS and confirm the style is recognizable; verify layout and typography at 375px and 1280px.

- [x] T011 [US2] Refine section and card styles in `docs/styles/main.css`: consistent spacing, rounded corners, subtle shadows, clear heading hierarchy for hero, features, install
- [x] T012 [US2] Ensure hero area and feature blocks in `docs/index.html` use CSS classes that apply Steam Deck–style (dark theme, accent for links/emphasis) from `docs/styles/main.css`
- [x] T013 [US2] Verify layout and typography scale in `docs/styles/main.css` at 375px, 768px, and 1280px without breaking (overflow, illegible text, or overlapping elements)

**Checkpoint**: User Story 2 is complete; the page has a cohesive Steam Deck/SteamOS visual identity and scales correctly.

---

## Phase 5: User Story 3 – Shareable and Embeddable Content (Priority: P2)

**Goal**: Page has a stable URL story; optional embed or deep-link support; no secrets or user-specific data in content.

**Independent Test**: Copy the page URL (after deployment) and open in another session; confirm same content; if embedding, confirm snippet or fragment renders; audit content for no tokens/keys/paths.

- [x] T014 [US3] Add fragment IDs to `docs/index.html` for deep linking and optional embed (e.g. `id="features"`, `id="install"`) per contracts/README embed snippet contract
- [x] T015 [US3] Document stable URL and publish steps in `specs/004-plugin-public-page/quickstart.md` (or confirm existing quickstart.md) so implementers know how to achieve FR-005
- [x] T016 [US3] Review `docs/index.html` and any embeddable content for FR-007/SC-005: no secrets, API keys, or user-specific paths; remove or replace if found

**Checkpoint**: User Story 3 is complete; page is shareable, optionally embeddable, and safe for public distribution.

---

## Phase 6: User Story 4 – Generated Images and Media (Priority: P2)

**Goal**: At least one hero/header image and one set of feature-related visuals (icons or images), Steam Deck–style, web-appropriate and legally safe.

**Independent Test**: Load the page; confirm at least one hero image and feature-related visuals are present; confirm alt text and that assets are appropriate for web and rights.

- [x] T017 [US4] Add at least one hero/header image under `docs/assets/` (e.g. hero.webp or hero.png), reference it in hero section of `docs/index.html` with `<img>` or `<picture>`, include non-empty `alt` text (FR-004, FR-008)
- [x] T018 [US4] Add feature-related visuals under `docs/assets/features/` (icons or images per major feature), reference them in the features section of `docs/index.html` with meaningful `alt` (FR-004, SC-002)
- [x] T019 [US4] Ensure all images in `docs/assets/` are web-appropriate (resolution, format, reasonable file size) and legally safe (original or permitted use); document source if needed (FR-009)

**Checkpoint**: User Story 4 is complete; the page has hero and feature media that match Steam Deck/SteamOS style and are suitable for web.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Accessibility, resilience when media fails, and quickstart validation.

- [x] T020 Ensure every image in `docs/index.html` has meaningful `alt` text and that critical content (plugin name, purpose, install link) remains available when images fail to load (FR-008, edge cases)
- [x] T021 Add fallback or placeholder behavior in `docs/index.html` or `docs/styles/main.css` for failed media (e.g. background color or text placeholder) so the page still communicates plugin identity
- [x] T022 Verify critical content (plugin name, purpose, install link) is available with JavaScript disabled and with minimal CSS (progressive enhancement; satisfies spec edge case "very old or restricted browser") in `docs/index.html`
- [x] T023 [P] Optional: Add responsive images in `docs/index.html` (e.g. `srcset` or `<picture>` with WebP + fallback) for hero and feature assets to improve performance per plan Performance Goals
- [x] T024 Run through quickstart.md: preview at 375px and 1280px, verify no secrets, confirm install link works; fix any gaps

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1. Blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2. Delivers MVP.
- **Phase 4 (US2)**: Depends on Phase 2; can run after or in parallel with Phase 3 (different files: CSS vs content).
- **Phase 5 (US3)**: Depends on Phase 2; benefits from Phase 3 content (fragment IDs, review).
- **Phase 6 (US4)**: Depends on Phase 2 and Phase 3 (structure and content to attach images to).
- **Phase 7 (Polish)**: Depends on Phases 3–6.

### User Story Dependencies

- **US1 (P1)**: After Foundational only. No dependency on US2/US3/US4.
- **US2 (P1)**: After Foundational only. Can be done in parallel with US1 (CSS vs HTML content).
- **US3 (P2)**: After Foundational; best after US1 so content exists to add fragment IDs and audit.
- **US4 (P2)**: After Foundational and US1 (need feature list and hero section to attach media).

### Parallel Opportunities

- T002 and T003 (Setup): different files.
- After Phase 2: T007–T010 (US1) can be done in one pass; T011–T013 (US2) can be done in parallel with US1 (CSS vs HTML).
- T014, T015, T016 (US3): T014 and T015 can run in parallel; T016 is a review task.
- T017, T018 (US4): different assets; T019 is review.
- T023 (Polish) is optional and [P].

---

## Parallel Example: User Story 1

```text
# Sequential within US1 (content in same file):
T007 Add plugin identity to index.html
T008 Add features section to index.html
T009 Add install section to index.html
T010 Verify readability at breakpoints (uses same CSS)
```

---

## Parallel Example: User Story 2

```text
# Can overlap with US1 (different file):
T011 Refine section/card styles in main.css
T012 Apply Steam Deck classes in index.html (may follow T007–T009)
T013 Verify layout at breakpoints in main.css
```

---

## Implementation Strategy

### MVP First (User Story 1 + Foundation)

1. Complete Phase 1 (Setup) and Phase 2 (Foundational).
2. Complete Phase 3 (User Story 1).
3. **Validate**: Open page; state plugin name, purpose, platform; see features and install link at 375px and 1280px.
4. Deploy or demo the minimal page.

### Incremental Delivery

1. Setup + Foundational → base page with theme and structure.
2. US1 → MVP (discover, understand, install path).
3. US2 → Full Steam Deck visual identity.
4. US3 → Shareable URL and no-secrets audit; optional embed.
5. US4 → Hero and feature media.
6. Polish → Alt text, fallbacks, quickstart check.

### Suggested MVP Scope

- **Phases 1 + 2 + 3** (Setup, Foundational, User Story 1). Delivers a working public page with correct content and basic Steam Deck styling; independently testable per SC-001 and install link accessibility.

---

## Notes

- [P] = safe to run in parallel (different files or independent changes).
- [USn] = task belongs to that user story for traceability.
- All paths are relative to repo root; use `docs/` as the page root.
- No automated test tasks: spec relies on manual visual and responsive checks.
- Commit after each task or after each user story checkpoint.
