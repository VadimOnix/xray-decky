# Data Model: Xray Decky Plugin UI Refactor (Decky/SteamOS UX)

**Branch**: `003-refactor-decky-ux`  
**Date**: 2026-02-03

## Entities

### 1) UI Layout State

- **Name**: `UILayout`
- **Values**:
  - `setup`: no saved connection configuration exists
  - `configured`: a saved connection configuration exists
- **Source of truth**: derived from persisted configuration existence.

### 2) Connection Configuration (summary view)

- **Name**: `ConnectionConfig`
- **Purpose**: represent the saved configuration in a way that can be shown in a compact “card”.
- **Key attributes (user-facing)**:
  - `exists` (boolean)
  - `displayName` (optional, human-readable)
  - `endpoint` (host + port) or equivalent minimal connection target summary
  - `isValid` (boolean) and `validationError` (optional)
  - `source` (e.g., “Imported link”) without exposing raw secrets by default

**Minimum summary shown in the Configured layout**:

- If available, show `displayName`.
- Always show `endpoint` (or a clearly labeled equivalent).
- Always show `isValid` status; if invalid, show `validationError`.

**Privacy/clarity rule**:

- The Configured layout MUST NOT display the full raw VLESS link by default (it may be available behind an explicit reveal/copy action if needed).

### 3) Connection State

- **Name**: `ConnectionState`
- **Values**:
  - `disconnected`
  - `connecting`
  - `connected`
  - `error`
  - `blocked` (kill switch active / traffic blocked)
- **Key attributes**:
  - `status` (enum above)
  - `message` (optional error/help text)
  - `connectedAt` (optional timestamp)
  - `uptime` (optional duration)

### 4) Options State

- **Name**: `OptionsState`
- **Fields**:
  - `tunEnabled` (boolean)
  - `tunActive` (boolean)
  - `tunHasPrivileges` (boolean)
  - `killSwitchEnabled` (boolean)
  - `killSwitchActive` (boolean)
  - `systemProxyEnabled` (boolean) — user preference for system proxy
  - `systemProxyActive` (boolean) — whether system proxy is currently applied (e.g. gsettings/kwriteconfig5)

### 5) Help Content

- **Name**: `HelpTopic`
- **Examples**:
  - `setup.qr_import`
  - `setup.lan_address`
  - `options.tun_mode`
  - `options.kill_switch`
  - `configured.reset`
- **Fields**:
  - `title`
  - `body` (short, scannable)

## State Transitions

### A) Setup → Configured

- **Trigger**: user taps “Save” with a valid VLESS link.
- **Expected**:
  - configuration becomes `exists=true`
  - UI layout becomes `configured`

### B) Configured → Setup

- **Trigger**: user taps “Reset configuration” while disconnected.
- **Expected**:
  - configuration is cleared (`exists=false`)
  - UI layout becomes `setup`

### C) Reset blocked while connected

- **Trigger**: user is connected and attempts to reset.
- **Expected**:
  - reset is disabled and cannot be executed

### D) Connection status updates

- **Trigger**: connect/disconnect actions or backend-driven state changes.
- **Expected**:
  - status bar reflects state within the plugin panel without reload

## Validation Rules (UI-facing)

- VLESS link must be non-empty and must pass format validation before save.
- “Reset configuration” is only actionable when connection status is not active (not connecting/connected/blocked).
