# Import Page HTTP API Contract

**Date**: 2026-01-30  
**Feature**: 002-vless-import-qr  
**Status**: Phase 1 Design

## Overview

The plugin backend runs an **HTTPS** server (aiohttp with TLS) on the Steam Deck, bound to `0.0.0.0:{port}` so devices on the home network can open the import page. TLS uses a self-signed certificate (generated on first run, stored in `DECKY_PLUGIN_RUNTIME_DIR`) so the page is in a secure context and `navigator.clipboard.readText()` (Paste) works. This document defines the HTTP(S) routes and request/response formats. Decky plugin methods remain as in frontend-backend-api; this contract is for the **web-accessible** import server only.

**Base URL**: `https://{steam deck local ip}:{port}`  
**Port**: From SettingsManager `importServer.port` (default 8765).  
**TLS**: Required; self-signed cert. On first visit the browser shows a certificate warning; user accepts once per device (e.g. "Advanced" → "Proceed to site").

---

## Routes

### 1. GET /import

**Purpose**: Serve the import page (HTML) so the user can paste/enter a VLESS link and submit.

**Response**:

- **Content-Type**: `text/html`
- **Body**: HTML document (e.g. `backend/static/import.html`) containing:
  - Form with: input (VLESS link), "Paste" button, "Save" button
  - Links to static assets: e.g. `/import/static/import.css`, optional `/import/static/import.js`
- **Status**: 200

**Notes**: No query parameters required. Page must work in mobile browsers (FR-007) and use Steam-consistent styling (FR-009).

---

### 2. GET /import/static/{path}

**Purpose**: Serve static assets (CSS, optionally JS) for the import page.

**Path**: `path` = filename, e.g. `import.css`, `import.js`.

**Response**:

- **Content-Type**: `text/css` for `.css`, `application/javascript` for `.js`
- **Body**: File contents from `backend/static/` (or equivalent)
- **Status**: 200 if found, 404 if not

---

### 3. POST /import

**Purpose**: Accept the VLESS link from the form and store it in the plugin (SettingsManager `vlessConfig`). Same validation and storage logic as the existing `import_vless_config` plugin method.

**Request**:

- **Content-Type**: `application/x-www-form-urlencoded` or `application/json`
- **Body (form)**: `link={VLESS_URL}` or `vless={VLESS_URL}` (single field)
- **Body (JSON)**: `{ "link": "vless://..." }` (optional; form is primary for simple HTML form)

**Response (success)**:

- **Status**: 200
- **Content-Type**: `application/json`
- **Body**: `{ "success": true, "message": "Saved" }` (or minimal JSON so the page can show "Saved" and optionally redirect or clear input)

**Response (validation error)**:

- **Status**: 400
- **Content-Type**: `application/json`
- **Body**: `{ "success": false, "error": "Invalid VLESS URL format" }` (or message from existing validation)

**Response (server error)**:

- **Status**: 500
- **Body**: `{ "success": false, "error": "..." }`

**Side effects**: On success, backend validates the link (same as `validate_vless_url` + parse + build_vless_config), then `settings.setSetting("vlessConfig", config)` and `settings.commit()`. Each successful POST overwrites the previous `vlessConfig`.

---

## Plugin methods used by frontend (Decky)

The plugin UI (Steam Deck frontend) does not call the HTTP server. It uses the **new Decky API** (api_version: 1):

- **get_vless_config**: To populate the link input with the current `config.sourceUrl` (after user returns from the import page or on mount).
- **get_import_server_url** (new): To build the QR code URL. Returns e.g. `{ "baseUrl": "https://192.168.x.x:8765", "path": "/import" }` so the frontend encodes `baseUrl + path` in the QR.

**get_import_server_url** (new backend method):

- **Frontend call**: `callable<[], ImportServerUrlResponse>('get_import_server_url')` from `@decky/api` at module scope; call the returned function (no args) when needed. Do **not** use `serverAPI.callPluginMethod`.
- **Backend returns**: `{ "baseUrl": "https://{lan_ip}:{port}", "path": "/import" }` where `lan_ip` is the host's LAN IP (not 127.0.0.1). Protocol MUST be **https** so the import page is in a secure context and Paste works.
- **Implementation**: Backend resolves LAN IP (e.g. outgoing socket to 8.8.8.8; fallbacks: `hostname -I`, `ip -4 route get 8.8.8.8`), reads port from `importServer.port` (default 8765), returns object with protocol https. No trailing slash on baseUrl.

---

## Security and validation

- All POST body input must be validated as a VLESS URL (reuse `validate_vless_url`, `parse_vless_url`, etc.) before writing to settings.
- Server must bind only to LAN (0.0.0.0) and MUST use TLS (self-signed certificate) so the page is in a secure context and Paste works from any device. Cert/key stored in `DECKY_PLUGIN_RUNTIME_DIR`; generated on first run or at startup if missing.
- No authentication on the import page (local network, single user); spec does not require auth.
