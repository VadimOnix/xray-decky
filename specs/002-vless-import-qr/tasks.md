# Tasks: VLESS Import via QR and Paste Form

**Input**: Design documents from `specs/002-vless-import-qr/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not requested in spec (manual on Steam Deck; optional pytest for backend). No test tasks included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **This project**: `main.py` at repo root; `backend/src/`, `backend/static/`; `src/` (frontend). Backend package: `backend/__init__.py`, `backend/src/__init__.py`. Deploy scripts: `deploy.sh`, `package-and-deploy.sh`. TLS cert/key: `DECKY_PLUGIN_RUNTIME_DIR` (e.g. cert.pem, key.pem).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependencies, directory structure, backend package layout, and TLS cert generation dependency for HTTPS import server.

- [X] T001 [P] Add aiohttp to backend Python dependencies in backend/requirements.txt; document in README that plugin runtime or install must install from it
- [X] T002 [P] Add cryptography to backend/requirements.txt for self-signed cert generation (plan, research §9); or document openssl-only path
- [X] T003 [P] Add QR code library to frontend in package.json (e.g. qrcode.react)
- [X] T004 Create directory backend/static for import page assets (import.html, import.css)
- [X] T005 [P] Create backend/__init__.py and backend/src/__init__.py so Python can import backend.src.* when plugin loads (spec Constraints & implementation)
- [X] T006 Add plugin root to sys.path in main.py before importing backend.*: insert PLUGIN_DIR = Path(__file__).resolve().parent and sys.path.insert(0, str(PLUGIN_DIR)) (spec Constraints & implementation)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: HTTPS import server (TLS, self-signed cert), cert storage/generation, settings, LAN IP resolution, import page so all user stories can use the same backend and page. Paste works from any device (secure context).

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T007 Ensure DECKY_PLUGIN_RUNTIME_DIR is used for cert storage in main.py; create runtime dir if missing when preparing to start import server (os.makedirs(runtime_dir, exist_ok=True))
- [X] T008 Implement cert generation: if cert.pem and key.pem are missing in DECKY_PLUGIN_RUNTIME_DIR, generate self-signed cert (cryptography or openssl subprocess), save cert.pem and key.pem to runtime dir; on failure log error and do not start import server (main.py or backend/src/cert_utils.py per plan)
- [X] T009 Create SSL context in main.py when starting import server: ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER), load_cert_chain(certfile, keyfile), set minimum TLS 1.2; on load failure log and do not start import server
- [X] T010 Implement reading ImportServerConfig (SettingsManager key importServer.port, default 8765, range 1024–65535) when starting the import server in main.py
- [X] T011 Implement get_import_server_url() in main.py: resolve LAN IP (not 127.0.0.1) via socket then fallbacks per research.md §8; read port from importServer.port; return { baseUrl: "https://{lan_ip}:{port}", path: "/import" }; register as plugin method (contracts/import-http-api.md)
- [X] T012 Create backend/src/import_server.py: aiohttp app with GET /import (serve HTML), GET /import/static/* (serve files from backend/static), POST /import handler; use relative imports from .config_parser; accept optional on_vless_saved callback and call it after successful Save (for backend emit)
- [X] T013 Wire POST /import in backend/src/import_server.py to validate_vless_url, parse_vless_url, build_vless_config and write to SettingsManager vlessConfig then commit; call on_vless_saved if provided; return 200 JSON on success, 400/500 with error on failure per contracts/import-http-api.md
- [X] T014 [P] Create backend/static/import.html with form: input for VLESS link, Paste control (icon left of input), Save button; POST to /import; link to /import/static/import.css; mobile-friendly; show error when POST returns 400
- [X] T015 [P] Create backend/static/import.css with Steam-consistent dark theme (FR-009) per spec design reference
- [X] T016 Start import HTTPS server in main.py Plugin._main(): use web.TCPSite(runner, "0.0.0.0", port, ssl_context=ssl_context); port from ImportServerConfig; stop server in Plugin._unload(); on cert gen/load failure do not start (plan HTTPS section)
- [X] T017 In main.py pass on_vless_saved callback to create_import_app that calls decky.emit("vless_config_updated") after Save so frontend can refresh config (spec reactive update)
- [X] T018 [P] Ensure deploy scripts include backend/__init__.py, backend/src/__init__.py, and backend/static/ (import.html, import.css) in package/deploy output (deploy.sh and package-and-deploy.sh per plan.md)

**Checkpoint**: Import server runs over HTTPS; GET /import serves the form; POST /import validates and stores; get_import_server_url() returns https LAN URL for QR; cert generated on first run; backend emits on Save. User stories can proceed.

---

## Phase 3: User Story 1 - Import VLESS via QR and Paste (Priority: P1) 🎯 MVP

**Goal**: User sees QR first, scans it, opens import page (https), uses Paste → Save, and the link is available in the plugin for connection setup.

**Independent Test**: User can complete: scan QR → open page (accept cert once) → Paste → Save → see the link available in the plugin for further setup.

### Implementation for User Story 1

- [X] T019 [P] [US1] In src/services/api.ts use callable() from @decky/api for get_import_server_url and other backend methods (no ServerAPI); export getImportServerUrl and use in components per contracts/import-http-api.md
- [X] T020 [P] [US1] Create src/components/QRImportBlock.tsx: call getImportServerUrl() from api.ts, render QR code (baseUrl + path) with qrcode.react, display import URL as text; no serverAPI prop
- [X] T021 [US1] In src/index.tsx use definePlugin from @decky/api with no arguments; return { name, content, icon, onDismount }; Content component renders QRImportBlock first then ConfigImport and rest (FR-001)
- [X] T022 [US1] Ensure plugin.json name matches Decky Loader registration (e.g. "Xray Decky") so frontend callables resolve to this plugin
- [X] T023 [US1] In src/components/ConfigImport.tsx subscribe to vless_config_updated via addEventListener from @decky/api and call loadStoredConfig when event fires; load getVLESSConfig on mount and show config.sourceUrl in the link input so imported link is visible after Save

**Checkpoint**: User Story 1 is complete: QR first (https URL), scan → Paste → Save → link in plugin; frontend uses new Decky API; UI updates on Save via backend emit.

---

## Phase 4: User Story 2 - Manual URL Entry Fallback (Priority: P2)

**Goal**: User can type or paste a VLESS link manually into the import form and Save; invalid/empty link shows a clear error and does not overwrite existing config.

**Independent Test**: User opens import page (via QR or URL), types or pastes a VLESS link, taps Save; link appears in plugin. Invalid/empty Save shows error on page; no overwrite.

### Implementation for User Story 2

- [X] T024 [P] [US2] Ensure backend POST /import returns 400 with JSON { success: false, error: "..." } for invalid or empty link in backend/src/import_server.py; do not overwrite vlessConfig
- [X] T025 [US2] Ensure import page displays validation error when POST /import returns 400 (show error in backend/static/import.html via response or minimal JS) so user can correct and retry

**Checkpoint**: User Story 2 is complete: manual entry works; invalid Save shows error, no overwrite.

---

## Phase 5: User Story 3 - Reliable Access to Import Page (Priority: P3)

**Goal**: User can reach the import page by scanning the QR or by opening the same URL manually in a browser when they know the Steam Deck IP and port.

**Independent Test**: With plugin running, user opens https://{steam deck LAN ip}:{port}/import in a browser and sees the same import form; QR scan encodes the same URL.

### Implementation for User Story 3

- [X] T026 [US3] Ensure import URL is displayed as copyable text in src/components/QRImportBlock.tsx (URL text visible and matches get_import_server_url baseUrl + path)
- [X] T027 [US3] Verify GET /import serves the same form when opened directly (no redirect or auth); document in quickstart or comment in backend/src/import_server.py

**Checkpoint**: User Story 3 is complete: direct URL and QR both open the same import page (https).

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and validation.

- [X] T028 [P] Ensure quickstart.md (or in-plugin hint) documents first-visit certificate warning: browser shows self-signed cert warning; user must accept once per device (e.g. "Advanced" → "Proceed to site"); after that Paste works (plan, spec Edge Cases)
- [ ] T029 Run quickstart.md validation on Steam Deck or same LAN (QR scan, accept cert once, Paste, Save, link in plugin; invalid Save error; direct URL access); optionally verify import page load &lt; 2s and submit &lt; 1s per plan Performance Goals; optionally verify full flow in under 30s (SC-001)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **User Stories (Phase 3–5)**: All depend on Foundational completion.
  - Can proceed sequentially (P1 → P2 → P3) or in parallel if staffed.
- **Polish (Phase 6)**: Depends on desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: After Phase 2 — no dependency on US2/US3.
- **User Story 2 (P2)**: After Phase 2 — same import page and backend; independently testable.
- **User Story 3 (P3)**: After Phase 2 — same URL and GET /import; independently testable.

### Within Each User Story

- US1: api.ts callable → QRImportBlock → index.tsx definePlugin + order → plugin.json name → ConfigImport + addEventListener vless_config_updated.
- US2: Backend 400 behavior then import page error display.
- US3: URL text visibility then GET /import direct access.

### Parallel Opportunities

- Phase 1: T001, T002, T003, T005 [P]; T004, T006 sequential.
- Phase 2: T014, T015, T018 [P] (different files).
- Phase 3: T019, T020 [P]; T021, T022, T023 sequential or T022 [P] with T019.
- Phase 4: T024 [P]; T025 depends on T024.
- Phase 6: T028 [P].

---

## Parallel Example: User Story 1

```bash
# After Phase 2, US1 implementation (parallel where possible):
Task T019: "src/services/api.ts use callable() from @decky/api"
Task T020: "Create src/components/QRImportBlock.tsx"
# Then T021 (index.tsx definePlugin + order), T022 (plugin.json), T023 (ConfigImport + addEventListener).
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (including cryptography for cert)
2. Complete Phase 2: Foundational (HTTPS server, cert gen, get_import_server_url https, emit on Save)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test scan → accept cert → Paste → Save → link in plugin
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → HTTPS server and import page working, LAN URL (https) in QR
2. Add User Story 1 → Test independently → MVP
3. Add User Story 2 → Error handling and manual entry → Test
4. Add User Story 3 → URL visibility and direct access → Test
5. Polish → Cert warning doc and quickstart validation

### Parallel Team Strategy

1. Complete Setup + Foundational together.
2. After Foundational:
   - Developer A: User Story 1 (api callable, QRImportBlock, index, plugin.json, ConfigImport + event listener)
   - Developer B: User Story 2 (400 + page error)
   - Developer C: User Story 3 (verify URL + direct GET)
3. Each story is independently testable.

---

## Notes

- [P] tasks = different files or no dependencies on incomplete work.
- [Story] label maps task to user story for traceability.
- Each user story is independently completable and testable.
- Commit after each task or logical group.
- Stop at any checkpoint to validate that story.
- All tasks use checklist format: `- [ ] [TaskID] [P?] [Story?] Description with file path`.
- HTTPS: cert in DECKY_PLUGIN_RUNTIME_DIR; baseUrl uses https; TCPSite with ssl_context; on cert failure do not start import server (plan, spec Clarifications 2026-01-31).
