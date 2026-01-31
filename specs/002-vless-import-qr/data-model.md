# Data Model: VLESS Import via QR and Paste Form

**Date**: 2026-01-30  
**Feature**: 002-vless-import-qr  
**Status**: Phase 1 Design

## Overview

This feature reuses the existing **VLESS Configuration** entity (see `specs/001-xray-vless-decky/data-model.md`) and adds minimal state for the import HTTP server. No new persistent entity is introduced for "import session"—each form submit overwrites the stored VLESS config.

---

## Entities

### 1. VLESS Configuration (existing)

**Purpose**: Stores the user's VLESS proxy configuration. Used by the plugin for connection setup.

**Storage**: SettingsManager key `vlessConfig` (unchanged).

**Relevance to this feature**:

- The import page POST submits a VLESS link; the backend validates it and writes the result to `vlessConfig` (same flow as `import_vless_config`).
- **Multiple imports**: Each successful Save overwrites `vlessConfig`. The plugin UI always uses the latest stored config; the link input is populated from `get_vless_config().config.sourceUrl`.
- Structure and validation rules remain as in 001 (VLESS URL format, UUID, port, etc.).

---

### 2. Import Server Config (new)

**Purpose**: Configuration for the HTTP server that serves the import page (port, optional future options).

**Storage**: SettingsManager key `importServer` (new).

**Structure**:

```typescript
interface ImportServerConfig {
  port: number // TCP port for HTTP server (default 8765)
  // Optional later: enabled?: boolean; bindAddress?: string;
}
```

**Validation Rules**:

- `port`: Integer 1024–65535 (non-privileged). Default 8765 if unset.

**Lifecycle**: Read at plugin start when starting the HTTP server; optional UI later to change port (then restart server or bind on next load).

---

### 2b. TLS certificate storage (runtime, not in SettingsManager)

**Purpose**: Persist the self-signed certificate and private key for the import server HTTPS so the same cert is reused across plugin restarts and the browser can remember the user's acceptance.

**Storage**: Filesystem under `DECKY_PLUGIN_RUNTIME_DIR` (e.g. `cert.pem`, `key.pem`). Directory created on first run if missing. Not stored in SettingsManager.

**Lifecycle**: Generated once when cert/key files are absent; then loaded at each plugin start. If generation or load fails, the import server MUST NOT start (optional: document HTTP fallback).

---

### 3. Import session (ephemeral, not stored)

**Purpose**: Describes one user flow: open import page → Paste/enter link → Save. No persistent entity.

**Behavior**: Each POST to the import server triggers validate → parse → build_vless_config → setSetting("vlessConfig", config) → commit. The "session" ends when the user leaves the page or saves again; the only persisted result is the updated `vlessConfig`.

---

## State flow

```
[Plugin started]
       ↓
[HTTPS server listens on 0.0.0.0:port with TLS]
[Frontend shows QR with https://{localIP}:{port}/import]
       ↓
[User scans QR → opens import page]
[User pastes/enters VLESS link → Save]
       ↓
[POST /import → validate → overwrite vlessConfig]
       ↓
[User returns to plugin UI]
[Frontend get_vless_config() → link input shows config.sourceUrl]
```

---

## Relationships

- **ImportServerConfig** is independent; used only to start the HTTP server.
- **VLESS Configuration** is the single source of truth for "current link"; both manual import (ConfigImport) and web form import write to it.
