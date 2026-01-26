<!--
Sync Impact Report:
Version: 0.0.0 (template) → 1.0.0 (initial)
Modified principles: N/A (initial creation)
Added sections:
  - Core Principles (8 principles)
  - Development Standards
  - Security & Performance Requirements
  - Distribution & Publishing Standards
Templates requiring updates:
  - ✅ plan-template.md (Constitution Check section aligned)
  - ✅ spec-template.md (no changes needed - structure compatible)
  - ✅ tasks-template.md (no changes needed - structure compatible)
Follow-up TODOs: None
-->

# Nekodeck Constitution

## Core Principles

### I. Standardized Project Structure
Every Decky Loader plugin MUST follow the official project structure:
- `src/` for frontend TypeScript code with `index.tsx` as entry point
- `backend/src/` for backend source code, `backend/out/` for compiled binaries
- `assets/` for images and resources
- `defaults/` for configuration files and templates (optional)
- `py_modules/` for Python modules (if used)
- Root-level `main.py` for Python backend (if used)
- Mandatory metadata files: `plugin.json`, `package.json`, `LICENSE(.md)`

**Rationale**: Consistent structure ensures compatibility with Decky Loader's build system, simplifies maintenance, and enables automated tooling.

### II. Mandatory Metadata Files
All plugins MUST include:
- `plugin.json`: Plugin name, author, flags, publish metadata (tags, description, PNG image)
- `package.json`: Lowercase name with hyphens, semantic version, optional `remote_binary` config
- `LICENSE(.md)`: Required for Plugin Store publication

**Rationale**: Metadata files are required by Decky Loader's plugin system and Plugin Store. Missing files prevent distribution and installation.

### III. Frontend Development Standards
Frontend development MUST use:
- **Node.js**: v16.14 or higher
- **pnpm**: Version 9 (mandatory, not optional)
- **@decky/ui**: Official React component library for Steam Deck UI
- TypeScript/React with `definePlugin` from `decky-frontend-lib`
- `ServerAPI` for backend communication via `callPluginMethod`

**Rationale**: Decky Loader's frontend infrastructure requires specific versions and libraries. Deviations cause build failures and UI inconsistencies.

### IV. Backend Development Patterns
Backend code MUST follow these patterns:
- Python `Plugin` class with async methods for frontend-callable functions
- `_main()` method for long-running code during plugin lifetime
- `_unload()` method for cleanup on plugin unload
- `SettingsManager` for persistent settings (never use `localStorage` directly in React)
- Binary outputs MUST be placed in `backend/out/` directory

**Rationale**: These patterns ensure proper lifecycle management, data persistence, and binary distribution compatibility.

### V. Build & Distribution Requirements
Distribution packages MUST include:
- `dist/index.js`: Compiled frontend bundle (MANDATORY)
- `plugin.json`, `package.json`, `LICENSE`: Metadata files (MANDATORY)
- `main.py`: Python backend if used (MANDATORY if backend exists)
- Binary files in `backend/out/` if backend uses compiled binaries
- Version in `package.json` MUST be updated before each PR

**Rationale**: Decky Loader's installation system requires specific file structure. Missing `dist/index.js` prevents plugin loading.

### VI. Security First
Security requirements:
- Flag `"root"` in `plugin.json` MUST only be used when absolutely necessary
- All user inputs MUST be validated before processing
- Use `SettingsManager` instead of direct filesystem access for settings
- For large binaries (>10MB), use `remote_binary` with SHA256 hash verification
- Install plugins only from trusted sources (official Plugin Store preferred)

**Rationale**: Root access increases security risk. Input validation prevents injection attacks. SettingsManager provides safe abstraction layer.

### VII. Semantic Versioning
Version management:
- Version in `package.json` MUST follow SemVer (MAJOR.MINOR.PATCH)
- Version MUST be updated before every PR that includes changes
- Include changelog in update descriptions
- Document breaking changes in MAJOR version bumps

**Rationale**: Consistent versioning enables dependency management, update tracking, and compatibility assessment.

### VIII. Real Device Testing
Testing requirements:
- Plugins MUST be tested on actual Steam Deck hardware, not just emulators
- Test compatibility with latest Decky Loader version before publication
- Test update scenarios before publishing updates
- Always update Decky Loader and plugins BEFORE updating Steam OS

**Rationale**: Steam Deck's unique environment (Game Mode, Desktop Mode, hardware constraints) cannot be fully emulated. Real device testing catches platform-specific issues.

## Development Standards

### Technology Stack
- **Frontend**: TypeScript, React, @decky/ui, decky-frontend-lib
- **Backend**: Python 3.x (asyncio for async operations)
- **Build Tools**: pnpm v9, TypeScript compiler
- **Package Manager**: pnpm (not npm or yarn)

### Code Quality
- Use official [Decky Plugin Template](https://github.com/SteamDeckHomebrew/decky-plugin-template) as starting point
- Follow React best practices for component structure
- Use async/await for all backend operations
- Minimize backend function calls from frontend (batch operations when possible)
- Remove unused dependencies to reduce plugin size

### Build Process
- Run `pnpm run build` after every frontend code change
- Use VSCode/VSCodium tasks: `setup`, `build`, `deploy`
- Update `@decky/ui` to latest version if build errors occur: `pnpm update @decky/ui --latest`
- Ensure `backend/out/` directory exists before building (create in Makefile/build script)

## Security & Performance Requirements

### Security Checklist
- [ ] Root flag avoided unless absolutely necessary
- [ ] All user inputs validated
- [ ] SettingsManager used for persistence (not direct filesystem)
- [ ] Remote binaries include SHA256 hash verification
- [ ] License file included in repository

### Performance Guidelines
- Minimize backend function calls (batch operations)
- Use asynchronous operations to avoid blocking
- Avoid blocking operations in `_main()` method
- Optimize images and resources
- Use `remote_binary` for files > 10MB to avoid zip size issues

## Distribution & Publishing Standards

### Pre-Publication Checklist
- [ ] All mandatory files present (`plugin.json`, `package.json`, `LICENSE`)
- [ ] Version in `package.json` updated
- [ ] Plugin tested on real Steam Deck
- [ ] Backend binaries (if any) in `backend/out/`
- [ ] README.md contains description and instructions
- [ ] Store image in PNG format
- [ ] Dependencies up to date (`pnpm update @decky/ui --latest`)
- [ ] Code follows community standards
- [ ] Root flag not used unnecessarily

### Publishing Process
1. Follow [decky-plugin-database](https://github.com/SteamDeckHomebrew/decky-plugin-database) instructions
2. Open Pull Request adding plugin as submodule
3. Verify all mandatory files present
4. Confirm version updated in `package.json`

### Installation Methods
- **Plugin Store**: Primary distribution method (requires PR to plugin database)
- **URL Installation**: Direct zip URL (Desktop Mode only, not Game Mode)

## Governance

This constitution supersedes all other development practices. All PRs and code reviews MUST verify compliance with these principles.

**Amendment Procedure**: 
- Amendments require documentation of rationale
- Version bump required (MAJOR for incompatible changes, MINOR for additions, PATCH for clarifications)
- Update dependent templates and documentation
- Include amendment in Sync Impact Report

**Compliance Review**:
- Constitution Check gate in implementation plans
- Pre-publication checklist validation
- Code review must verify principle adherence

**Complexity Justification**: Any deviation from these principles requires explicit justification in implementation plans, documenting why simpler alternatives are insufficient.

**Version**: 1.0.0 | **Ratified**: 2026-01-26 | **Last Amended**: 2026-01-26
