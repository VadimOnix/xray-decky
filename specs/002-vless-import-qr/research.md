# Research: VLESS Import via QR and Paste Form

**Feature**: 002-vless-import-qr  
**Date**: 2026-01-30  
**Status**: Phase 0 complete

## 1. HTTP server for import page

**Decision**: Use **aiohttp** in the backend to run an async HTTP server that serves the import page and handles POST.

**Rationale**:

- Backend is already async (Plugin async methods); aiohttp fits without blocking the event loop.
- Single dependency; no separate process. Server is started in `Plugin._main()` and stopped in `_unload()`.
- Can bind to `0.0.0.0` so devices on the home network can open the page.
- Supports `FileResponse` for HTML and `add_static()` for CSS/JS; one route for GET `/import`, one for POST (form submit), static prefix for assets.

**Alternatives considered**:

- **Python stdlib `http.server`**: Synchronous; would require a thread to avoid blocking. Rejected in favor of a single async stack.
- **Flask/FastAPI**: Heavier; not needed for one HTML page and one POST. Rejected to keep the plugin light.
- **Separate Node/static server**: Extra process and port. Rejected; backend already has access to SettingsManager and validation.

---

## 2. Port and binding

**Decision**: Use a **configurable port** with a **default** (e.g. 8765). Store in SettingsManager under a key like `importServer.port`. Bind to `0.0.0.0:{port}` so the page is reachable from the LAN (Steam Deck IP + port in QR).

**Rationale**: Fixed default allows QR to be built without user config; optional setting allows avoiding conflicts with other services.

**Alternatives considered**:

- **Random free port**: Would require the frontend to fetch the port from the backend for QR; adds a backend method. Accepted as optional later; default port is simpler for MVP.
- **Port 80**: Requires root or capabilities; rejected (Constitution: no root).

---

## 3. Form submit → plugin UI

**Decision**: **No push**. Web form POSTs to the HTTP server; server validates the VLESS link and writes to SettingsManager (`vlessConfig`), same as existing `import_vless_config`. Plugin UI (ConfigImport) already loads config on mount via `get_vless_config()` and shows `config.sourceUrl` in the link input. User returns to the plugin after Save; when the panel is shown, frontend already refetches on mount, so the latest link is displayed. Optional: refetch when panel gains focus (if Decky exposes it).

**Rationale**: Decky has no built-in push from backend to frontend. Polling adds complexity for little gain: the main flow is “Save on phone → open plugin on Deck → see new link.” Refetch on mount is enough; multiple imports each overwrite `vlessConfig`, so “each time use new link” is satisfied.

**Alternatives considered**:

- **Polling get_vless_config every N seconds**: Possible but unnecessary for typical use; can be added later if needed.
- **WebSocket**: Overkill for a single “link saved” signal; rejected.

---

## 4. Static assets layout

**Decision**: Place import page assets under **`backend/static/`** (or `backend/static/import/`): `import.html`, `import.css`, optional `import.js`. Server serves GET `/import` with the HTML (or redirects `/import` → `/import/` and serve `import.html`); GET `/import/static/*` via `add_static()` so CSS/JS can be loaded with relative paths (e.g. `/import/static/import.css`). HTML form POSTs to `/import` (same path or `/import/save`).

**Rationale**: Keeps static files next to the backend that serves them; no frontend build step for the import page (plain HTML/CSS/JS). Steam-consistent styling (FR-009) is done in CSS (dark theme, contrast).

**Alternatives considered**:

- **Assets in repo root `assets/import/`**: Possible; serving from `backend/static/` keeps all import-server concerns in backend.
- **Inline CSS in HTML**: One file is simpler but less maintainable; separate CSS is preferred for Steam-like styling.

---

## 5. Multiple imports

**Decision**: **Overwrite**. Each successful POST replaces `vlessConfig` in SettingsManager. No history list; “use new link each time” means “last saved link is the one used.” Spec and edge cases already state this.

**Rationale**: Matches spec (“repeated Saves overwrite or update the imported link”); keeps implementation and UI simple.

---

## 6. QR code generation (frontend)

**Decision**: Use a **small QR library** in the frontend (e.g. `qrcode.react` or similar) to encode the import URL `http://{ip}:{port}/import`. IP and port must be supplied by the backend (e.g. `get_import_server_url()` returning `{ baseUrl: "http://192.168.x.x:8765", path: "/import" }`). Backend gets local IP from the system (e.g. default route interface or first non-loopback) and reads port from settings.

**Rationale**: QR generated on the Deck avoids round-trip to a third-party service; URL is fully under our control. Backend already has access to network and settings.

**Alternatives considered**:

- **Backend returns a PNG of the QR**: Possible but requires an image-over-HTTP or base64 API; frontend QR is simpler and responsive.
- **Hardcoded IP**: Wrong on multi-NIC or VPN; backend must resolve local IP.

---

## 7. Frontend–backend API (Decky)

**Decision**: Use the **new Decky API** (api_version: 1). Entry: `definePlugin` from `@decky/api` with **no arguments**. Backend calls: `callable<[args], ReturnType>("method_name")` from `@decky/api` at module scope; call the returned function when needed. Do **not** use `decky-frontend-lib` `serverAPI` or `callPluginMethod` passed into `definePlugin`.

**Rationale**: Validated during debugging: when the loader did not pass serverAPI (or passed it in a form the plugin did not handle), the UI did not receive backend responses (QR block stuck on "Loading..."). Switching to the new API (callable from @decky/api) fixed the issue. Plugin name in `plugin.json` must match loader registration (e.g. "Xray Decky").

**Alternatives considered**:

- **serverAPI.callPluginMethod**: Caused UI to hang; loader may not provide serverAPI reliably for api_version: 1.
- **decky-frontend-lib definePlugin(serverAPI)**: Same; spec "Constraints & implementation" documents the correct approach.

---

## 8. Backend Python structure and LAN IP

**Decision**: (1) Plugin root on `sys.path` before importing `backend.*` (e.g. in `main.py`, insert `PLUGIN_DIR`). (2) Package `backend` and `backend/src` MUST have `__init__.py`; deployment MUST include them. (3) QR URL host: backend MUST return **LAN IP** (not 127.0.0.1). Resolve via: outgoing socket to 8.8.8.8; if that yields 127.0.0.1 or fails, fallback to `hostname -I` or `ip -4 route get 8.8.8.8` (parse `src`).

**Rationale**: Without sys.path and __init__.py, backend failed to load (ModuleNotFoundError: backend). Without LAN IP, QR pointed to 127.0.0.1 and the phone could not open the import page. Fallbacks ensure LAN IP on SteamOS even when socket method fails.

**Alternatives considered**:

- **No sys.path**: Backend failed at load; Decky runs main.py with CWD/import path such that `backend` is not found unless plugin dir is on sys.path.
- **127.0.0.1 in QR**: Spec and user require URL openable from other devices on same network; 127.0.0.1 is not.

---

## Summary table

| Topic            | Decision                        | Rationale / note                     |
| ---------------- | ------------------------------- | ------------------------------------ |
| HTTP server      | aiohttp                         | Async, single process, static + POST |
| Port             | Configurable, default e.g. 8765 | LAN access, no root                  |
| Form → UI        | Refetch on mount                | No push; overwrite vlessConfig       |
| Static assets    | backend/static/                 | Served by same server                |
| Multiple imports | Overwrite vlessConfig           | Spec-compliant, simple               |
| QR generation    | Frontend lib + backend URL API  | Backend provides baseUrl + path      |
| Frontend–backend | @decky/api definePlugin + callable | Validated; serverAPI caused UI hang  |
| Backend structure | sys.path + __init__.py          | Required for backend package load    |
| LAN IP for QR    | Socket + hostname -I + ip route | Not 127.0.0.1; reachable from LAN   |
| HTTPS / Paste    | TLS with self-signed cert       | Secure context → clipboard.readText |

---

## 9. HTTPS for import page (Paste from any device)

**Decision**: Serve the import page over **HTTPS** with a **self-signed certificate** so that the browser treats the page as a secure context and `navigator.clipboard.readText()` (Paste) works when the page is opened from another device (phone/PC) on the LAN.

**Rationale**:

- On HTTP, browsers do not expose the Clipboard API (readText) to pages opened from a non-localhost origin; Paste fails with "not supported" or permission errors.
- HTTPS (even with a self-signed cert) establishes a secure context; after the user accepts the certificate warning once per device, Paste works.
- Cert storage in `DECKY_PLUGIN_RUNTIME_DIR` keeps cert/key out of version control and follows Decky runtime data layout. Generate on first run or at startup if files are missing.
- aiohttp supports `TCPSite(..., ssl_context=ssl_context)`; Python stdlib `ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)` and `load_cert_chain(certfile, keyfile)` are sufficient. Prefer TLS 1.2+.
- On certificate generation or load failure: log the error and do not start the import server (spec: MUST NOT start). Optional: document or implement HTTP fallback as a degraded mode (Paste then only works via manual paste hint).

**Implementation (source of truth)**: Cert generation uses **OpenSSL subprocess only** (no `cryptography`). Decky Loader runtime does not install `backend/requirements.txt`; the sandbox may bundle an `openssl` binary and libs in PATH/`LD_LIBRARY_PATH` that require libssl/libcrypto versions not present on SteamOS. Implementation: call **system** `/usr/bin/openssl` on Linux; run subprocess with env that omits `LD_LIBRARY_PATH` and `LD_PRELOAD` so the loader uses system libssl/libcrypto. Implemented in `backend/src/cert_utils.py`.

**Alternatives considered**:

- **HTTP only**: Paste does not work from another device; rejected per spec FR-002 and user clarification.
- **Public CA cert**: Requires domain and CA issuance; overkill for local import page. Self-signed is acceptable; one-time acceptance per device is documented.
- **Cert generation at build time**: Possible but runtime generation keeps one less build step and works on any Deck without pre-bundled certs.
- **cryptography library**: Would require installing backend deps in Decky runtime; rejected in favor of system OpenSSL subprocess for zero extra Python deps.
