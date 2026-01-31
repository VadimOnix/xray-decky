# Implementation Plan: VLESS Import via QR and Paste Form

**Branch**: `002-vless-import-qr` | **Date**: 2026-01-31 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/002-vless-import-qr/spec.md`

## Summary

User can import a VLESS link via a self-hosted import page: scan QR from the plugin → open page in browser → Paste (clipboard) → Save → link appears in the plugin. The import page MUST be served over **HTTPS** with a self-signed certificate so that `navigator.clipboard.readText()` (Paste) works from any device on the LAN. Backend: aiohttp with TLS (cert/key in `DECKY_PLUGIN_RUNTIME_DIR`), LAN IP in QR URL, `get_import_server_url()` returns `https://{lan_ip}:{port}`. Frontend: QR block first, `callable()` from `@decky/api`; backend emits `vless_config_updated` after Save so UI updates without manual refresh.

## Technical Context

**Language/Version**: Python 3.x (asyncio), TypeScript/React  
**Primary Dependencies**: aiohttp (HTTPS with ssl.SSLContext), system OpenSSL via subprocess for cert generation (no cryptography), @decky/api (callable, addEventListener), qrcode.react  
**Storage**: SettingsManager (vlessConfig, importServer.port); TLS cert/key files in `DECKY_PLUGIN_RUNTIME_DIR` (cert.pem, key.pem)  
**Testing**: Manual on Steam Deck; optional pytest for backend validation  
**Target Platform**: Steam Deck (Decky Loader), Linux; import page opened in mobile/desktop browsers on same LAN  
**Project Type**: Decky plugin (frontend `src/`, backend `main.py` + `backend/src/`, static `backend/static/`)  
**Performance Goals**: Import page load &lt; 2s, POST &lt; 1s; full flow (scan → Paste → Save) &lt; 30s (SC-001)  
**Constraints**: No root; bind 0.0.0.0; TLS 1.2+; cert generated on first run or at startup if missing; on cert failure do not start import server (optional HTTP fallback documented)  
**Scale/Scope**: Single user, single Steam Deck; import server one port, one page

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Standardized Project Structure**: Yes — `src/` frontend, `main.py` + `backend/src/`, `backend/static/`, plugin.json, package.json, LICENSE.
- **II. Mandatory Metadata Files**: Yes — plugin.json, package.json, LICENSE present.
- **III. Frontend Development Standards**: **Violation** — Using `definePlugin` from `@decky/api` with no arguments and `callable()` for backend calls (not decky-frontend-lib ServerAPI). Justified: loader did not provide serverAPI reliably; new API validated during debugging (see spec Constraints & research §7).
- **IV. Backend Development Patterns**: Yes — Plugin class, _main()/_unload(), SettingsManager; import server started in _main(), stopped in _unload().
- **V. Build & Distribution Requirements**: Yes — dist/index.js, version in package.json; deploy includes backend/__init__.py, backend/src/__init__.py, backend/static/.
- **VI. Security First**: Yes — No root; input validated (VLESS URL); SettingsManager for config; TLS for import page (self-signed cert in runtime dir).
- **VII. Semantic Versioning**: Yes — Version updated before PR; SemVer.
- **VIII. Real Device Testing**: Yes — Test on Steam Deck (QR scan, Paste, Save, cert acceptance).

**Violations**: III (Frontend API) — see Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/002-vless-import-qr/
├── plan.md              # This file
├── research.md          # Phase 0 (includes HTTPS/TLS decisions)
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1 (includes cert warning for user)
├── contracts/           # import-http-api.md (HTTPS base URL)
│   └── import-http-api.md
└── tasks.md             # Phase 2 (/speckit.tasks)
```

### Source Code (repository root)

```text
main.py                  # Plugin entry; _main() starts HTTPS import server, get_import_server_url returns https
backend/
├── __init__.py
├── requirements.txt     # aiohttp only; cert via system openssl (no cryptography)
├── static/             # import.html, import.css
└── src/
    ├── __init__.py
    ├── import_server.py   # aiohttp app; no TLS here (main.py passes ssl_context to TCPSite)
    ├── config_parser.py
    ├── error_codes.py
    └── cert_utils.py    # Generate/load cert via OpenSSL subprocess (system /usr/bin/openssl, clean env)
src/
├── index.tsx           # definePlugin from @decky/api; QRImportBlock first
├── components/
│   ├── QRImportBlock.tsx
│   ├── ConfigImport.tsx  # addEventListener('vless_config_updated') → loadStoredConfig
│   └── ...
└── services/
    └── api.ts          # callable() for get_import_server_url, get_vless_config, etc.
```

**Structure Decision**: Decky plugin with backend (Python) and frontend (TypeScript/React). Import server is part of the backend process; TLS cert/key stored under `DECKY_PLUGIN_RUNTIME_DIR` (e.g. `.../data/xray-decky/`). Cert generation on first run or at startup if files missing; aiohttp `TCPSite` started with `ssl_context` in `main.py`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **III** (definePlugin no args, callable from @decky/api) | Loader did not provide serverAPI reliably; UI hung on "Loading..." when using callPluginMethod. | Using serverAPI caused broken frontend–backend communication; new API is the validated fix (spec Clarifications & research §7). |

## HTTPS for Import Page (Paste over network)

- **Cert storage**: `DECKY_PLUGIN_RUNTIME_DIR` (or env equivalent); create dir if missing. Files: `cert.pem`, `key.pem`.
- **Cert generation**: On first run or at startup if cert/key missing — use **system OpenSSL** via subprocess only (no `cryptography`). On Linux use `/usr/bin/openssl`; subprocess env MUST omit `LD_LIBRARY_PATH` and `LD_PRELOAD` so the Decky sandbox’s bundled libs are not loaded (they require libssl/libcrypto versions not present on SteamOS). Save `cert.pem` and `key.pem` to runtime dir; subject/CN localhost; validity e.g. 365 days. Implemented in `backend/src/cert_utils.py`.
- **SSL context**: `ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)`; load cert and key; set minimum version TLS 1.2.
- **aiohttp**: `web.TCPSite(runner, "0.0.0.0", port, ssl_context=ssl_context)` (or equivalent aiohttp API for HTTPS).
- **get_import_server_url()**: Return `{ "baseUrl": "https://{lan_ip}:{port}", "path": "/import" }`.
- **Documentation**: quickstart (and optionally in-plugin hint): on first visit browser shows certificate warning; user clicks "Advanced" → "Proceed to site" once per device; after that Paste works.
- **Error handling**: If cert generation or load fails — log error, do not start import server. Optional: fallback to HTTP on same or different port (document in plan/spec); default is no start.
- **Dependencies**: **aiohttp only** in `backend/requirements.txt`. Cert generation uses system OpenSSL (no extra Python dependency); document in README or requirements.txt comment that the plugin relies on system `openssl` for TLS cert generation.
