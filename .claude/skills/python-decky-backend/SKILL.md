---
name: python-decky-backend
description: Python asyncio patterns for this plugin's backend — main.py wiring vs py_modules domain logic, RPC dict conventions, background tasks and the supervisor pattern, subprocess-managed proxy cores, the embedded aiohttp HTTPS server, SettingsManager, and the pytest harness style. Use when writing or reviewing backend code (main.py, py_modules/backend/src/), adding RPC methods or background tasks, managing core processes, or writing backend tests.
---

# Python backend (asyncio) for this plugin

Platform basics (Decky lifecycle, `decky` module, env dirs) → `decky-plugin-dev` skill. This skill is how **this** backend is built.

## Layering rule

- `main.py` = wiring only: Decky lifecycle (`_main`, `_unload`), sys.path setup for `py_modules/` (that's why ruff ignores `E402` there), settings bootstrap, and thin RPC methods that delegate.
- Domain logic lives in `py_modules/backend/src/*` as plain modules with no Decky imports — that's what makes them unit-testable on any machine (`conftest.py` just adds `py_modules/` to `sys.path`).
- New feature = new module in `backend/src/` + thin `Plugin` method + pytest file. Don't grow logic inside `main.py`.

## RPC conventions

- Every frontend-callable method is `async`, returns a JSON-safe dict, and **never raises across the boundary** — catch and return `{"success": False, "error": "<message>", ...}` (error codes in `error_codes.py`). Frontend types in `src/services/api.ts` must mirror the shape.
- Methods must return fast; anything slow (downloads, latency tests) runs as a background task and reports via `decky.emit(...)` events or a status-poll method.

## Background work & the supervisor pattern

- Long-lived loops start in `_main` via `asyncio.create_task(...)` (e.g. `_subscription_refresh_loop`) and are cancelled in `_unload`. A loop must be a no-op unless the user enabled the feature.
- `supervisor.py` is the template for process babysitting: policy injected as async callables (`wait_for_exit`, `on_crash`, `restart`, …) so tests drive it without real processes; **fail closed first** (engage kill switch on crash, then attempt restart); bounded exponential backoff; give up cleanly after repeated crash episodes instead of flapping.
- Proxy cores (xray/sing-box) are subprocesses owned by their manager (`xray_manager.py` / `singbox_manager.py`); binaries are self-healing — SteamOS can wipe `bin/` on system updates, so `_main` re-downloads missing binaries (pins in `*_version.json`) into a persistent dir.

## Embedded aiohttp server (import page + admin panel)

- HTTPS with a self-signed cert generated into `DECKY_PLUGIN_RUNTIME_DIR` (`cert_utils.ensure_cert_key`), TLS ≥1.2. If cert setup fails — don't start the server, log and continue; the plugin must work without it.
- Port from settings (default 8765, clamped 1024–65535), try next ports if busy. Bind host follows the "Allow LAN access" setting: `0.0.0.0` vs `127.0.0.1`.
- Static assets: repo tree serves `defaults/static/`, installed builds serve `<plugin>/static/` — resolve both, in that order.

## Settings

Module-level `SettingsManager(name="settings", settings_directory=$DECKY_PLUGIN_SETTINGS_DIR)`, `settings.read()` once at import; `getSetting(key, default)` / `setSetting` + `commit()`. All persistence goes here — the frontend has no storage.

## Testing (pytest)

- Style: plain `def test_*` that build an `async def scenario()` and run it; scriptable **harness classes** with injected callables instead of mocking modules (see `tests/test_supervisor.py`). No network, no real processes, no Deck needed.
- Parsers/exporters (`config_parser`, `importer`, `exporter`) are pure-function heavy — test with real share-link fixtures (vless://, ss://, …).
- Run: `pytest tests/`, single: `pytest tests/test_supervisor.py -k backoff`. Lint: `ruff check py_modules/ tests/ main.py conftest.py` — the rule set is pinned in `pyproject.toml`, don't widen in passing.

## SteamOS gotchas

Immutable filesystem, no runtime pip installs — everything ships inside `py_modules/`. Network-mode code (TUN, kill switch, system proxy) has OS-level constraints documented in `steamos network restrictions.md` — read it before touching those modules; they can only be fully verified on a real Deck.
