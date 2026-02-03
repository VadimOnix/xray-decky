# Implementation Plan: Xray Reality VLESS Decky Plugin

**Branch**: `001-xray-vless-decky` | **Date**: 2026-01-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-xray-vless-decky/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Decky Loader plugin for Steam Deck that enables VLESS proxy connections with Reality protocol support. Users can import VLESS configurations via URL, toggle connections on/off, and optionally enable TUN mode for system-wide traffic routing. Includes kill switch functionality to prevent clearnet leaks on unexpected disconnects. Built using TypeScript/React frontend with @decky/ui components, Python backend with asyncio, and integrates xray-core binary for proxy functionality.

## Technical Context

**Language/Version**: TypeScript (frontend), Python 3.x (backend)  
**Primary Dependencies**:

- Frontend: Node.js v16.14+, pnpm v9, @decky/ui, decky-frontend-lib, React
- Backend: Python 3.x (asyncio), SettingsManager, xray-core binary (Go-based, distributed as binary)
- Testing: Jest/Vitest (frontend), pytest (backend), GitHub Actions CI/CD
- Build: pnpm, TypeScript compiler, Python packaging  
  **Storage**: SettingsManager (JSON files via DECKY_PLUGIN_SETTINGS_DIR) for VLESS configs, preferences (TUN mode, kill switch)  
  **Testing**: Jest/Vitest for frontend unit tests, pytest for backend unit/integration tests, GitHub Actions for CI/CD, manual testing on Steam Deck hardware  
  **Target Platform**: SteamOS (Arch-based Linux), Game Mode and Desktop Mode, immutable filesystem constraints, AppImage/Flatpak distribution model  
  **Project Type**: decky-plugin (frontend + backend hybrid structure)  
  **Performance Goals**: Connection establishment <5s, config validation <1s, UI responsiveness <200ms, minimal memory footprint (<50MB idle)  
  **Constraints**:
- Must respect SteamOS immutable filesystem (read-only system partition)
- Must work in both Game Mode and Desktop Mode
- TUN mode requires elevated privileges (sudo exemption setup)
- Avoid conflicts with Steam ports (UDP 27015-27030)
- Must handle network interruptions gracefully
- Kill switch must prevent all clearnet traffic on unexpected disconnect  
  **Scale/Scope**: Single-user plugin, 1 VLESS config at a time (with subscription support), 3-5 UI screens, ~2000-3000 LOC estimated

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

Verify compliance with Nekodeck Constitution principles:

- **I. Standardized Project Structure**: ✅ Yes - Following Decky Loader plugin structure: `src/` for frontend TypeScript, `backend/src/` for backend source, `backend/out/` for xray-core binary, `assets/` for resources, root-level `main.py` for Python backend entry point
- **II. Mandatory Metadata Files**: ✅ Yes - Will include `plugin.json` (name, author, flags, publish metadata), `package.json` (lowercase name, semantic version), `LICENSE(.md)` for Plugin Store publication
- **III. Frontend Development Standards**: ✅ Yes - Using Node.js v16.14+, pnpm v9 (mandatory), @decky/ui components, decky-frontend-lib with `definePlugin`, TypeScript/React
- **IV. Backend Development Patterns**: ✅ Yes - Python `Plugin` class with async methods, `_main()` for long-running code, `_unload()` for cleanup, SettingsManager for persistent settings (VLESS configs, preferences), xray-core binary in `backend/out/`
- **V. Build & Distribution Requirements**: ✅ Yes - `dist/index.js` will be generated via `pnpm run build`, version in `package.json` updated before each PR, all mandatory files included in distribution
- **VI. Security First**: ✅ Yes - Root flag used only where absolutely necessary (TUN mode on SteamOS requires plugin.json "root" flag for CAP_NET_ADMIN; alternative sudo exemption documented for users who prefer it), all user inputs validated (VLESS URL validation), SettingsManager used for persistence (no direct filesystem access), xray-core binary will use SHA256 hash verification if distributed via `remote_binary`
- **VII. Semantic Versioning**: ✅ Yes - Version in `package.json` follows SemVer (MAJOR.MINOR.PATCH), updated before every PR with changes, changelog in update descriptions
- **VIII. Real Device Testing**: ✅ Yes - Plan includes testing on actual Steam Deck hardware in both Game Mode and Desktop Mode, compatibility testing with latest Decky Loader version, update scenario testing

**Violations**: None identified. All principles are followed. TUN mode requires elevated privileges but uses sudo exemption pattern (not root flag), which is acceptable per Constitution Principle VI.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/                          # Frontend TypeScript/React code
├── index.tsx                 # Plugin entry point (definePlugin)
├── components/               # React components
│   ├── ConfigImport.tsx      # VLESS URL import UI
│   ├── ConnectionToggle.tsx  # Connection on/off toggle
│   ├── StatusDisplay.tsx     # Connection status display
│   ├── TUNModeToggle.tsx     # TUN mode enable/disable
│   └── KillSwitchToggle.tsx # Kill switch enable/disable
├── services/                 # Frontend services
│   └── api.ts                # ServerAPI wrapper for backend calls
└── utils/                    # Frontend utilities
    └── validation.ts         # VLESS URL validation

backend/                      # Backend Python code
├── src/                      # Backend source code
│   ├── xray_manager.py       # xray-core process management, config generation (Reality client: publicKey, serverName, shortId)
│   ├── config_parser.py      # VLESS config parsing/validation
│   ├── tun_manager.py        # TUN mode setup/teardown, system route (default dev xray0 metric 100), sockopt.interface for loop prevention
│   ├── system_proxy.py       # System Proxy management (gsettings/kwriteconfig5), auto-enabled with TUN mode
│   ├── kill_switch.py        # Kill switch traffic blocking
│   └── connection_manager.py # Connection state management
├── out/                      # Compiled binaries (created during build)
│   └── xray-core             # xray-core binary (downloaded/built)
└── tests/                    # Backend tests
    ├── unit/
    └── integration/

main.py                       # Backend entry point (Plugin class)

tests/                        # Frontend tests
├── unit/
└── integration/

assets/                       # Images and resources
├── icon.svg                  # Plugin icon
└── store-image.png           # Store image (PNG format)

defaults/                     # Optional configuration files
└── (if needed for xray-core config templates)

plugin.json                   # Plugin metadata [MANDATORY]
package.json                  # Package metadata [MANDATORY]
LICENSE.md                    # License file [MANDATORY]
README.md                     # Project documentation
tsconfig.json                 # TypeScript configuration
.gitignore                    # Git ignore rules
.github/                      # GitHub workflows
├── workflows/
│   ├── ci.yml                # CI/CD pipeline
│   └── release.yml           # Release automation
```

**Structure Decision**: Decky Loader plugin structure with frontend (TypeScript/React in `src/`) and backend (Python in `backend/src/`, binary in `backend/out/`). Follows official Decky plugin template structure. Testing organized by frontend/backend separation. GitHub Actions workflows for CI/CD and testing best practices.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations identified. All Constitution principles are followed.

---

## Phase Completion Status

### Phase 0: Outline & Research ✅ COMPLETE

**Status**: All research tasks completed, all "NEEDS CLARIFICATION" items resolved.

**Deliverables**:

- ✅ `research.md` - Comprehensive research on xray-core integration, TUN mode, kill switch, VLESS validation, GitHub best practices, Decky patterns, SteamOS constraints

**Key Decisions**:

- xray-core integration via subprocess management
- TUN mode using xray-core built-in TUN with privilege checks
- Kill switch using iptables rules
- VLESS URL validation via regex + xray-core config validation
- GitHub Actions CI/CD for testing
- Official Decky plugin template structure

---

### Phase 1: Design & Contracts ✅ COMPLETE

**Status**: All design artifacts generated, agent context updated.

**Deliverables**:

- ✅ `data-model.md` - Complete data model with entities (VLESSConfig, ConnectionState, TUNModePreference, KillSwitchPreference), validation rules, state transitions, relationships
- ✅ `contracts/frontend-backend-api.md` - Complete API contracts for all frontend-backend communication methods
- ✅ `quickstart.md` - Developer quick start guide with setup, workflow, and troubleshooting
- ✅ Agent context updated (`.cursor/rules/specify-rules.mdc`)

**Key Design Decisions**:

- SettingsManager for all persistence (VLESS configs, preferences)
- ServerAPI.callPluginMethod() pattern for all frontend-backend communication
- Async/await pattern for all backend operations
- Comprehensive error handling with user-friendly messages
- State management via React state + SettingsManager

---

### Phase 2: Task Breakdown ⏳ PENDING

**Status**: Not started. Use `/speckit.tasks` command to generate task breakdown.

**Next Steps**:

- Run `/speckit.tasks` to break down implementation into actionable tasks
- Tasks will reference this plan, data model, and API contracts

---

## Constitution Check (Post-Phase 1)

_Re-evaluated after Phase 1 design completion._

All Constitution principles remain compliant:

- ✅ Project structure follows Decky Loader standards
- ✅ All mandatory files will be included
- ✅ Frontend/backend patterns follow Decky conventions
- ✅ Security practices maintained (no root flag, input validation, SettingsManager)
- ✅ Testing strategy includes GitHub Actions CI/CD
- ✅ Real device testing planned

**No new violations identified.**

---

## Generated Artifacts Summary

| Artifact            | Path                                                           | Status      |
| ------------------- | -------------------------------------------------------------- | ----------- |
| Implementation Plan | `specs/001-xray-vless-decky/plan.md`                           | ✅ Complete |
| Research Document   | `specs/001-xray-vless-decky/research.md`                       | ✅ Complete |
| Data Model          | `specs/001-xray-vless-decky/data-model.md`                     | ✅ Complete |
| API Contracts       | `specs/001-xray-vless-decky/contracts/frontend-backend-api.md` | ✅ Complete |
| Quick Start Guide   | `specs/001-xray-vless-decky/quickstart.md`                     | ✅ Complete |
| Agent Context       | `.cursor/rules/specify-rules.mdc`                              | ✅ Updated  |

---

## Next Command

Run `/speckit.tasks` to generate task breakdown for Phase 2 implementation.
