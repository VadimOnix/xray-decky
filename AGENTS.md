# AGENTS.md

Guidance for AI coding agents working in this repository. `CLAUDE.md` imports this file; other agents (Codex, Gemini CLI, opencode, …) read it natively.

## What this project is

**xray-decky** — a [Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader) plugin: VPN/proxy client for Steam Deck. Supports VLESS (REALITY), VMess, Trojan, Shadowsocks, Hysteria2 and TUIC via two swappable cores (xray-core and sing-box), plus TUN mode, kill switch and system proxy for Gaming Mode.

Two halves, one plugin:

- **Frontend** (`src/`, TypeScript/React): the Quick Access Menu panel. Bundled by Rollup (`@decky/rollup`) into `dist/index.js`. React itself is provided by the Steam client at runtime — that's why `react`/`react-dom` are ignored peer deps and only `@types/react` is pinned.
- **Backend** (`main.py` + `py_modules/backend/src/`, Python 3.11+ asyncio): loaded by Decky Loader; `main.py` defines the `Plugin` class whose async methods are the RPC surface.

## Commands

Package manager is **pnpm 9** (mandatory), Node.js 18+.

```bash
pnpm install               # also required once per fresh git worktree
pnpm run build             # rollup → dist/index.js
pnpm run watch             # rebuild on save
pnpm test                  # vitest (frontend + web admin panel), tests/frontend/
pnpm test tests/frontend/i18n.test.ts   # single frontend test file
pnpm run lint              # eslint + prettier check
pnpm run lint:ts           # tsc --noEmit for src/ and the test tsconfig
pnpm run lint:fix          # eslint --fix + prettier --write
```

Python side (deps: `pip install -r requirements-dev.txt`):

```bash
pytest tests/                                  # backend unit tests
pytest tests/test_config_parser.py -k reality  # single file / test
ruff check py_modules/ tests/ main.py conftest.py
```

Deploy to a real Steam Deck over SSH (details in `docs/DEVELOPMENT.md`):

```bash
pnpm run deploy            # build + rsync to the Deck (DECK_RESTART=1 to restart Decky)
pnpm run package           # build + zip + upload zip to the Deck
pnpm run package:local     # build + zip locally, no device needed
```

Deploy scripts read `DECK_HOST`, `DECK_PLUGINS_DIR`, `DECK_RESTART`, `DECK_UPLOAD_DIR` from the environment or from a gitignored `.deckdeployrc` in the repo root. All three commands share the same staging step (`scripts/stage-plugin.sh`), so the on-device file set always matches the packaged one.

## Architecture

### Frontend ↔ backend contract

- All backend calls go through `@decky/api` `callable()`. Typed wrappers live **only** in [src/services/api.ts](src/services/api.ts) — components never call `callable()` directly.
- Backend→frontend push uses `decky.emit(...)` (Python) + `addEventListener` (TS).
- Persistence is Decky `SettingsManager` on the backend (never `localStorage` in React).

### Backend layout

`main.py` is the wiring/entry layer (Decky lifecycle: `_main`, `_unload`; sys.path setup for `py_modules/` — hence the `E402` ruff ignore for `main.py`). Domain logic lives in `py_modules/backend/src/`:

- `xray_manager.py` / `singbox_manager.py` — the two proxy cores; `supervisor.py` restarts a crashed core; `connection_manager.py` holds connection state
- `config_parser.py` / `importer.py` / `exporter.py` — share-link (vless://, ss://, …) and subscription parsing; `profile_store.py` — multi-profile storage; `refresh_scheduler.py` — subscription auto-refresh
- `tun_manager.py`, `kill_switch.py`, `system_proxy.py` — system-level network modes
- `import_server.py` + `admin_api.py` — an aiohttp HTTPS server (self-signed cert via `cert_utils.py`) serving the QR/browser import page and the web admin panel
- `xray_downloader.py` / `singbox_downloader.py` — self-healing core binaries, versions pinned in `xray_version.json` / `singbox_version.json`; binaries persist across plugin updates
- `stats.py`, `latency.py`, `update_checker.py` — traffic stats, profile latency tests, update checks

### Frontend layout

`src/index.tsx` (entry) → `components/layouts/SetupLayout.tsx` or `ConfiguredLayout.tsx` depending on whether a config exists. Panel state is centralized in `hooks/usePluginPanelState.ts`. i18n in `utils/i18n.ts`.

### Web admin panel

`defaults/static/` (admin.html + admin.js) is a **no-build** browser JS app served by the backend aiohttp server — it ships to the device as-is. It is covered by the vitest suite (`tests/frontend/admin-panel-*.test.ts` boot the real files in jsdom).

### Tests

- `tests/` (pytest) — backend modules; `conftest.py` inserts `py_modules/` into `sys.path` (Decky CLI layout).
- `tests/frontend/` (vitest, jsdom) — frontend pure logic + the web admin panel.

## Conventions and gotchas

- **Ruff rule set is pinned** (`select = ["E4","E7","E9","F"]` in `pyproject.toml`) — do not widen it in passing; widening is a deliberate change with the fallout fixed in the same commit.
- **A `package.json` version bump on `master` is the release act**: auto-release workflow tags `v<version>` and publishes. CI refuses a version without a matching `CHANGELOG.md` section. Use `scripts/prepare-release.sh <version>`; see `docs/RELEASING.md`.
- CHANGELOG follows Keep a Changelog; new work goes under `[Unreleased]`.
- SteamOS has an immutable filesystem and network quirks — see `steamos network restrictions.md` before touching TUN/kill-switch/system-proxy code.
- Decky plugin platform specifics (plugin.json flags, packaging layout, store rules): `decky-loader-plugin-best-practices.md`.

## Feature workflow

Feature work follows the [superpowers](https://github.com/obra/superpowers) skills: brainstorm before designing, write an implementation plan before coding, execute plans with TDD. Plans and design notes live in `docs/superpowers/`. `specs/NNN-slug/` is a **read-only archive** of past features from the earlier spec-kit workflow — useful as decision history, not a template for new work.

## Active Technologies

- TypeScript/React 19 (frontend, `src/`) + @decky/ui, @decky/api, qrcode.react
- Python 3.11+ asyncio (backend, `py_modules/backend/`) + aiohttp, cryptography
- Decky SettingsManager for persistence; no database
