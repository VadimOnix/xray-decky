# Tasks: Xray Reality VLESS Decky Plugin

**Input**: Design documents from `/specs/001-xray-vless-decky/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Tests are OPTIONAL - not explicitly requested in spec, so test tasks are not included. Focus on implementation tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., [US1], [US2], [US3], [US4])
- Include exact file paths in descriptions

## Path Conventions

- **Frontend**: `src/` at repository root
- **Backend**: `backend/src/` for Python source, `backend/out/` for xray-core binary
- **Tests**: `tests/` for frontend, `backend/tests/` for backend
- **Root files**: `main.py`, `plugin.json`, `package.json`, `LICENSE.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (src/, backend/src/, backend/out/, assets/, tests/, backend/tests/)
- [X] T002 [P] Initialize frontend project with package.json (Node.js v16.14+, pnpm v9, @decky/ui, decky-frontend-lib, React, TypeScript)
- [X] T003 [P] Create plugin.json with plugin metadata (name, author, flags, publish metadata)
- [X] T004 [P] Create LICENSE.md file (required for Plugin Store publication)
- [X] T005 [P] Create tsconfig.json for TypeScript configuration
- [X] T006 [P] Create .gitignore with Decky Loader patterns
- [X] T007 [P] Create README.md with project documentation
- [X] T008 [P] Setup GitHub Actions workflows (.github/workflows/ci.yml, .github/workflows/release.yml)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T009 Create main.py with Plugin class structure (async methods, \_main(), \_unload())
- [X] T010 [P] Setup SettingsManager integration in main.py (read DECKY_PLUGIN_SETTINGS_DIR, initialize SettingsManager)
- [X] T011 [P] Create backend/src/ directory structure
- [X] T012 Download or build xray-core binary and place in backend/out/xray-core (make executable)
- [X] T013 [P] Create src/index.tsx with definePlugin entry point (basic structure, no components yet)
- [X] T014 [P] Create src/services/api.ts with ServerAPI wrapper skeleton
- [X] T015 Create backend/src/connection_manager.py skeleton (ConnectionState management)
- [X] T016 Create error handling infrastructure (error codes, user-friendly messages)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Import VLESS config via URL (Priority: P1) 🎯 MVP

**Goal**: Users can import and store VLESS configuration via URL (single node or subscription). This is the foundation for all other flows.

**Independent Test**: Enter a valid VLESS URL, confirm it is stored, verify the config is available for connection. Delivers value even if connect/toggle are not yet implemented.

### Implementation for User Story 1

- [X] T017 [P] [US1] Create backend/src/config_parser.py with VLESS URL parsing logic (regex pattern, UUID validation, port validation)
- [X] T018 [US1] Implement VLESS URL validation in backend/src/config_parser.py (validate format, UUID v4, hostname/IP, port range 1-65535)
- [X] T019 [US1] Implement subscription URL parsing in backend/src/config_parser.py (base64 decode, JSON array parsing, extract single node)
- [X] T020 [US1] Implement import_vless_config backend method in main.py (call config_parser, validate, store via SettingsManager)
- [X] T021 [US1] Implement get_vless_config backend method in main.py (retrieve from SettingsManager)
- [X] T022 [US1] Implement validate_vless_config backend method in main.py (re-validate stored config)
- [X] T023 [P] [US1] Create src/utils/validation.ts with frontend VLESS URL validation helper (regex check before backend call)
- [X] T024 [P] [US1] Create src/components/ConfigImport.tsx component (input field, submit button, error display)
- [X] T025 [US1] Implement ConfigImport component logic (call import_vless_config API, handle success/error, show stored config)
- [X] T026 [US1] Add ConfigImport component to src/index.tsx plugin content
- [X] T027 [US1] Implement error handling in ConfigImport (invalid URL format, invalid UUID, invalid port, network errors)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Users can import VLESS configs and see them stored.

---

## Phase 4: User Story 2 - Connection on/off toggle (Priority: P2)

**Goal**: Users can turn the proxy connection on or off via a toggle in the plugin UI. Connection state is clearly displayed.

**Independent Test**: Enable the toggle (connection starts), disable it (connection stops), confirm traffic flows or stops as expected. Delivers value with or without TUN mode.

### Implementation for User Story 2

- [X] T028 [P] [US2] Create backend/src/xray_manager.py with xray-core process management (start, stop, monitor process)
- [X] T029 [US2] Implement xray-core config file generation in backend/src/xray_manager.py (convert VLESSConfig to xray-core JSON config, avoid Steam ports UDP 27015-27030 for local listeners)
- [X] T030 [US2] Implement xray-core subprocess spawning in backend/src/xray_manager.py (asyncio.create_subprocess_exec, handle stdout/stderr)
- [X] T031 [US2] Implement xray-core process monitoring in backend/src/xray_manager.py (check if process is alive, handle crashes)
- [X] T032 [US2] Implement toggle_connection backend method in main.py (load config, validate, start/stop xray-core via xray_manager)
- [X] T033 [US2] Implement get_connection_status backend method in main.py (return current status, process ID, uptime)
- [X] T034 [US2] Update backend/src/connection_manager.py with ConnectionState management (track status, timestamps, process ID)
- [X] T035 [P] [US2] Create src/components/ConnectionToggle.tsx component (toggle switch, connection status display)
- [X] T036 [US2] Implement ConnectionToggle component logic (call toggle_connection API, poll get_connection_status, handle errors)
- [X] T037 [P] [US2] Create src/components/StatusDisplay.tsx component (show connection status: disconnected/connecting/connected/error)
- [X] T038 [US2] Add ConnectionToggle and StatusDisplay components to src/index.tsx
- [X] T039 [US2] Implement error handling in ConnectionToggle (no config, invalid config, xray-core process failed, network errors)
- [X] T040 [US2] Implement connection state persistence in connection_manager.py (save status to SettingsManager for UI restoration)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Users can import configs and toggle connections.

---

## Phase 5: User Story 4 - Installation and privileges (Priority: P2)

**Goal**: Installation process supports adding plugin's AppImage to sudo exemption list for TUN mode functionality.

**Independent Test**: Complete installation (including sudo exclude and run-as-admin steps), then enable TUN and verify it works without password prompts.

### Implementation for User Story 4

- [X] T041 [P] [US4] Create installation documentation in README.md (sudo exemption setup steps, AppImage configuration)
- [X] T042 [US4] Implement check_tun_privileges backend method in main.py (test TUN interface creation, check CAP_NET_ADMIN)
- [X] T043 [US4] Create backend/src/tun_manager.py skeleton (privilege checking, TUN interface management)
- [X] T044 [US4] Implement privilege check logic in backend/src/tun_manager.py (attempt TUN creation test, detect insufficient privileges)
- [X] T045 [US4] Implement get_tun_mode_status backend method in main.py (return privilege status, TUN interface info)
- [X] T046 [P] [US4] Create installation script or guide for sudo exemption (document /etc/sudoers.d/ configuration)

**Checkpoint**: Installation and privilege checking infrastructure ready. TUN mode can now be implemented.

---

## Phase 6: User Story 3 - TUN mode for system-wide tunneling (Priority: P3)

**Goal**: Users can enable TUN mode to route all system traffic through the VLESS proxy. Requires elevated privileges.

**Independent Test**: Enable TUN mode (when plugin has privileges), run a game or system app, confirm traffic is tunneled. Delivers value for users who need global routing.

### Implementation for User Story 3

- [X] T047 [US3] Implement TUN mode configuration in backend/src/xray_manager.py (add TUN outbound to xray-core config when enabled)
- [X] T048 [US3] Implement TUN interface creation in backend/src/tun_manager.py (use xray-core built-in TUN support via config)
- [X] T049 [US3] Implement TUN mode teardown in backend/src/tun_manager.py (cleanup TUN interface on disable/disconnect)
- [X] T050 [US3] Implement toggle_tun_mode backend method in main.py (check privileges, update preference, validate)
- [X] T051 [US3] Update toggle_connection to respect TUN mode preference (include TUN config in xray-core config when enabled)
- [X] T052 [US3] Update connection_manager.py to handle TUN mode state (track TUN interface, privilege status)
- [X] T053 [P] [US3] Create src/components/TUNModeToggle.tsx component (toggle switch, privilege status display, error messages)
- [X] T054 [US3] Implement TUNModeToggle component logic (call toggle_tun_mode API, check privileges, handle insufficient privileges error)
- [X] T055 [US3] Add TUNModeToggle component to src/index.tsx
- [X] T056 [US3] Implement error handling in TUNModeToggle (insufficient privileges, TUN creation failed, guidance messages)
- [X] T057 [US3] Update SettingsManager persistence for TUN mode preference (store enabled state, privilege status)

**Checkpoint**: All user stories should now be independently functional. Users can import configs, toggle connections, and enable TUN mode (with proper installation).

---

## Phase 7: Kill Switch (Cross-cutting with User Story 2)

**Goal**: Optional kill switch that blocks all system traffic when proxy disconnects unexpectedly. Off by default.

**Independent Test**: Enable kill switch, disconnect proxy unexpectedly, verify all traffic is blocked, verify user is notified, verify reconnection restores traffic.

### Implementation for Kill Switch

- [X] T058 [P] Create backend/src/kill_switch.py with iptables rule management (apply rules, remove rules, track rule IDs)
- [X] T059 Implement kill switch activation in backend/src/kill_switch.py (apply iptables DROP rules, allow xray-core process)
- [X] T060 Implement kill switch deactivation in backend/src/kill_switch.py (remove iptables rules, restore normal routing)
- [X] T061 Implement unexpected disconnect detection in backend/src/connection_manager.py (monitor xray-core process, detect crashes)
- [X] T062 Implement kill switch activation on unexpected disconnect in connection_manager.py (check preference, call kill_switch.activate)
- [X] T063 Implement toggle_kill_switch backend method in main.py (update preference, activate/deactivate if needed)
- [X] T064 Implement get_kill_switch_status backend method in main.py (return enabled state, active state, activation timestamp)
- [X] T065 Implement deactivate_kill_switch backend method in main.py (manual deactivation, remove iptables rules)
- [X] T066 [P] Create src/components/KillSwitchToggle.tsx component (toggle switch, active state display, blocked message)
- [X] T067 Implement KillSwitchToggle component logic (call toggle_kill_switch API, show blocked state, handle errors)
- [X] T068 Add KillSwitchToggle component to src/index.tsx
- [X] T069 Implement notification system for kill switch activation (toast notification when traffic is blocked)
- [X] T070 Update connection_manager.py to handle kill switch on reconnect (deactivate when connection restored)
- [X] T071 Update SettingsManager persistence for kill switch preference (store enabled state, active state)

**Checkpoint**: Kill switch fully functional. System blocks traffic on unexpected disconnect, user is notified, can reconnect or disable.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T072 [P] Update README.md with complete usage instructions (import config, toggle connection, enable TUN, kill switch, port conflict considerations - avoid Steam ports UDP 27015-27030)
- [X] T073 [P] Add error message improvements across all components (user-friendly, actionable messages)
- [X] T074 [P] Implement connection state persistence across plugin restarts (restore UI state from SettingsManager)
- [X] T075 [P] Add connection metrics display (bytes sent/received, uptime) in StatusDisplay component
- [X] T076 [P] Implement config replacement flow in ConfigImport (show existing config, allow replacement)
- [X] T077 [P] Add validation feedback improvements (real-time validation, clear error messages)
- [X] T078 [P] Code cleanup and refactoring (extract common patterns, improve error handling)
- [X] T079 [P] Add logging throughout backend (log connection events, errors, state changes)
- [ ] T080 [P] Create assets/icon.svg for plugin icon
- [ ] T081 [P] Create assets/store-image.png for Plugin Store (PNG format, required dimensions)
- [X] T082 [P] Update plugin.json with complete publish metadata (tags, description, image URL)
- [X] T083 [P] Update package.json with correct version (SemVer format, update before PR)
- [X] T084 [P] Validate quickstart.md instructions against actual implementation
- [ ] T085 [P] Test on actual Steam Deck hardware (Game Mode and Desktop Mode)
- [X] T086 [P] Test plugin restart scenarios (verify state persistence)
- [ ] T087 [P] Test SteamOS update scenarios (verify installation persistence)
- [ ] T088 [P] Validate performance goals (connection establishment <5s, config validation <1s, UI responsiveness <200ms, memory footprint <50MB idle) during real device testing

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - Can start immediately after Phase 2
- **User Story 2 (Phase 4)**: Depends on Foundational + User Story 1 (needs config import)
- **User Story 4 (Phase 5)**: Depends on Foundational - Can start in parallel with US2 (different components)
- **User Story 3 (Phase 6)**: Depends on Foundational + User Story 4 (needs privilege checking) + User Story 2 (needs connection toggle)
- **Kill Switch (Phase 7)**: Depends on Foundational + User Story 2 (needs connection management)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories ✅ MVP
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) + User Story 1 (needs config to connect)
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Independent, but needed for US3
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) + User Story 4 (privileges) + User Story 2 (connection)
- **Kill Switch**: Can start after Foundational (Phase 2) + User Story 2 (connection management)

### Within Each User Story

- Backend methods before frontend components
- Core implementation before error handling
- Basic functionality before polish
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes:
  - User Story 1 can start immediately
  - User Story 4 can start in parallel with User Story 1 (different components)
- Within User Story 1: T017, T023, T024 can run in parallel (different files)
- Within User Story 2: T028, T035, T037 can run in parallel (different files)
- Within User Story 3: T053 can run in parallel with backend work
- Within Kill Switch: T058, T066 can run in parallel (different files)
- All Polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all parallel tasks for User Story 1 together:
Task: "Create backend/src/config_parser.py with VLESS URL parsing logic"
Task: "Create src/utils/validation.ts with frontend VLESS URL validation helper"
Task: "Create src/components/ConfigImport.tsx component"
```

---

## Parallel Example: User Story 2

```bash
# Launch all parallel tasks for User Story 2 together:
Task: "Create backend/src/xray_manager.py with xray-core process management"
Task: "Create src/components/ConnectionToggle.tsx component"
Task: "Create src/components/StatusDisplay.tsx component"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Import VLESS config)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

**MVP Deliverable**: Users can import and store VLESS configurations. Foundation for all other features.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Basic proxy functionality)
4. Add User Story 4 → Test independently → Deploy/Demo (TUN preparation)
5. Add User Story 3 → Test independently → Deploy/Demo (Full TUN support)
6. Add Kill Switch → Test independently → Deploy/Demo (Complete feature set)
7. Polish → Final release

Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Import config)
   - Developer B: User Story 4 (Privileges) - can start in parallel
3. After User Story 1 completes:
   - Developer A: User Story 2 (Connection toggle)
   - Developer B: Continue User Story 4
4. After User Story 2 and 4 complete:
   - Developer A: User Story 3 (TUN mode)
   - Developer B: Kill Switch
5. Both complete → Polish phase together

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- xray-core binary must be in backend/out/ before connection tasks
- SettingsManager is used for all persistence (never direct filesystem access)
- All backend methods are async and return dict with success/error fields
- Frontend uses ServerAPI.callPluginMethod() for all backend communication

---

## Task Summary

- **Total Tasks**: 87
- **Phase 1 (Setup)**: 8 tasks
- **Phase 2 (Foundational)**: 8 tasks
- **Phase 3 (User Story 1 - MVP)**: 11 tasks
- **Phase 4 (User Story 2)**: 13 tasks
- **Phase 5 (User Story 4)**: 6 tasks
- **Phase 6 (User Story 3)**: 11 tasks
- **Phase 7 (Kill Switch)**: 14 tasks
- **Phase 8 (Polish)**: 17 tasks

**MVP Scope (Phases 1-3)**: 27 tasks  
**Full Feature Scope**: 88 tasks

**Parallel Opportunities**: ~30 tasks marked [P] can run in parallel with other tasks
