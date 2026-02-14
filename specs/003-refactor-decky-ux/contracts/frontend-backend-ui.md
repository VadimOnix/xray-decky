# Contract: Frontend ↔ Backend UI API (Xray Decky)

**Branch**: `003-refactor-decky-ux`  
**Date**: 2026-02-03  
**Purpose**: Define the callable methods and events required by the refactored two-state UI layout.

## Transport / Model

- Frontend calls backend via Decky callable methods (typed calls).
- Backend may emit events to notify frontend of state changes (e.g. config updated).

## Callables

### Configuration

#### `get_vless_config() -> { exists: boolean, config?: VLESSConfig }`

- **Use**: Determine `UILayout` (setup vs configured) and show config summary card.
- **Notes**: `exists=false` means Setup layout.

#### `import_vless_config(url: string) -> { success: boolean, config?: VLESSConfig, error?: string }`

- **Use**: Manual Save in Setup layout.
- **Success**: persists configuration; emits config-updated event.
- **Failure**: MUST NOT overwrite a previously valid saved configuration; returns actionable error.

#### `reset_vless_config() -> { success: boolean, error?: string }` _(new / required)_

- **Use**: Reset configuration action in Configured layout.
- **Preconditions**:
  - MUST fail (or be rejected) if an active connection exists.
- **Success**:
  - clears persisted config
  - emits config-updated event so UI switches to Setup

### Connection state / actions

#### `get_connection_status() -> { status: ConnectionStatus, errorMessage?: string, connectedAt?: number, uptime?: number }`

- **Use**: Status bar.

#### `toggle_connection(enable: boolean) -> { success: boolean, status: ConnectionStatus, error?: string }`

- **Use**: Primary Connect/Disconnect action.

### Options

#### `get_tun_mode_status() -> { enabled: boolean, hasPrivileges: boolean, isActive: boolean, tunInterface?: string }`

- **Use**: TUN toggle row + state.

#### `toggle_tun_mode(enabled: boolean) -> { success: boolean, enabled: boolean, hasPrivileges: boolean, error?: string }`

- **Use**: TUN toggle.

#### `get_kill_switch_status() -> { enabled: boolean, isActive: boolean, activatedAt?: number }`

- **Use**: Kill Switch toggle row + state.

#### `toggle_kill_switch(enabled: boolean) -> { success: boolean, enabled: boolean }`

- **Use**: Kill Switch toggle.

#### `deactivate_kill_switch() -> { success: boolean, error?: string }`

- **Use**: Explicit unblock action when kill switch is active (if UI exposes it).

### System Proxy _(delivered in branch)_

#### `toggle_system_proxy(enabled: boolean) -> { success: boolean, enabled: boolean, error?: string, socksPort?: number | null, httpPort?: number | null }`

- **Use**: Toggle system-wide proxy (GNOME gsettings / KDE kwriteconfig5). When enabled, configures HTTP/SOCKS to 127.0.0.1 (default ports 10809/10808). Typically used when connection is active; cleared on disconnect.
- **Notes**: Backend uses `SystemProxyManager`; preference persisted in SettingsManager under `systemProxy`.

#### `get_system_proxy_status() -> { enabled: boolean, isActive: boolean, socksPort?: number | null, httpPort?: number | null, address?: string | null, error?: string }`

- **Use**: Status row for System Proxy toggle (user preference and actual proxy state).

### Setup helper

#### `get_import_server_url() -> { baseUrl: string, path: string }`

- **Use**: QR + LAN address shown in Setup layout.

## Events

### `vless_config_updated` _(already used by frontend)_

- **Emitted when**:
  - configuration is saved via import page (external browser)
  - configuration is saved via manual Save in Setup layout
  - configuration is reset/cleared
- **Frontend behavior**:
  - refetch config and re-evaluate UI layout

## Compatibility Notes

- New API split: frontend uses `@decky/api` (callables/events) and `@decky/ui` (UI components) per Deckbrew migration guidance:
  - `https://wiki.deckbrew.xyz/en/plugin-dev/new-api-migration`
