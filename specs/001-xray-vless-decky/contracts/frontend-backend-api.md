# Frontend-Backend API Contracts

**Date**: 2026-01-26  
**Feature**: 001-xray-vless-decky  
**Status**: Phase 1 Design

## Overview

This document defines the API contracts between the TypeScript/React frontend and Python backend for the Xray Reality VLESS Decky Plugin. All communication uses Decky Loader's `ServerAPI.callPluginMethod()` pattern.

---

## API Methods

### 1. Config Management

#### `import_vless_config`

**Purpose**: Import and validate a VLESS configuration URL.

**Frontend Call**:

```typescript
const result = await serverAPI.callPluginMethod('import_vless_config', {
  url: string, // VLESS URL (single node or subscription)
})
```

**Backend Signature**:

```python
async def import_vless_config(self, url: str) -> dict:
    """
    Import and validate VLESS configuration URL.

    Args:
        url: VLESS URL string (vless://... or base64 subscription)

    Returns:
        {
            'success': bool,
            'config': VLESSConfig | None,
            'error': str | None
        }
    """
```

**Response Format**:

```typescript
interface ImportConfigResponse {
  success: boolean
  config?: {
    sourceUrl: string
    configType: 'single' | 'subscription'
    uuid: string
    address: string
    port: number
    name?: string
    isValid: boolean
    // ... other VLESSConfig fields
  }
  error?: string // Error message if success is false
}
```

**Error Cases**:

- Invalid URL format → `success: false, error: "Invalid VLESS URL format"`
- Invalid UUID → `success: false, error: "Invalid UUID format"`
- Invalid port → `success: false, error: "Port must be between 1 and 65535"`
- Network error (subscription fetch) → `success: false, error: "Failed to fetch subscription"`

---

#### `get_vless_config`

**Purpose**: Retrieve stored VLESS configuration.

**Frontend Call**:

```typescript
const result = await serverAPI.callPluginMethod('get_vless_config', {})
```

**Backend Signature**:

```python
async def get_vless_config(self) -> dict:
    """
    Get stored VLESS configuration.

    Returns:
        {
            'config': VLESSConfig | None,
            'exists': bool
        }
    """
```

**Response Format**:

```typescript
interface GetConfigResponse {
  config?: VLESSConfig // Stored config or null
  exists: boolean // Whether config exists
}
```

---

#### `validate_vless_config`

**Purpose**: Re-validate stored VLESS configuration.

**Frontend Call**:

```typescript
const result = await serverAPI.callPluginMethod('validate_vless_config', {})
```

**Backend Signature**:

```python
async def validate_vless_config(self) -> dict:
    """
    Re-validate stored VLESS configuration.

    Returns:
        {
            'isValid': bool,
            'error': str | None
        }
    """
```

**Response Format**:

```typescript
interface ValidateConfigResponse {
  isValid: boolean
  error?: string // Error message if invalid
}
```

---

### 2. Connection Management

#### `toggle_connection`

**Purpose**: Turn proxy connection on or off.

**Frontend Call**:

```typescript
const result = await serverAPI.callPluginMethod('toggle_connection', {
  enable: boolean, // true to connect, false to disconnect
})
```

**Backend Signature**:

```python
async def toggle_connection(self, enable: bool) -> dict:
    """
    Toggle proxy connection on/off.

    Args:
        enable: True to connect, False to disconnect

    Returns:
        {
            'success': bool,
            'status': str,  # 'connected', 'disconnected', 'error'
            'error': str | None,
            'processId': int | None
        }
    """
```

**Response Format**:

```typescript
interface ToggleConnectionResponse {
  success: boolean
  status: 'connected' | 'disconnected' | 'error'
  error?: string
  processId?: number // xray-core process PID if connected
}
```

**Error Cases**:

- No config stored → `success: false, error: "No VLESS config stored"`
- Config invalid → `success: false, error: "VLESS config is invalid"`
- TUN mode enabled but no privileges → `success: false, error: "TUN mode requires elevated privileges"`
- xray-core process failed → `success: false, error: "Failed to start xray-core"`
- Network error → `success: false, error: "Connection failed"`

---

#### `get_connection_status`

**Purpose**: Get current connection status.

**Frontend Call**:

```typescript
const result = await serverAPI.callPluginMethod('get_connection_status', {})
```

**Backend Signature**:

```python
async def get_connection_status(self) -> dict:
    """
    Get current connection status.

    Returns:
        {
            'status': str,  # 'disconnected', 'connecting', 'connected', 'error', 'blocked'
            'connectedAt': int | None,  # Unix timestamp
            'errorMessage': str | None,
            'processId': int | None,
            'uptime': int | None  # Seconds
        }
    """
```

**Response Format**:

```typescript
interface ConnectionStatusResponse {
  status: 'disconnected' | 'connecting' | 'connected' | 'error' | 'blocked'
  connectedAt?: number
  errorMessage?: string
  processId?: number
  uptime?: number // Connection uptime in seconds
}
```

---

### 3. TUN Mode Management

#### `toggle_tun_mode`

**Purpose**: Enable or disable TUN mode preference.

**Frontend Call**:

```typescript
const result = await serverAPI.callPluginMethod('toggle_tun_mode', {
  enabled: boolean,
})
```

**Backend Signature**:

```python
async def toggle_tun_mode(self, enabled: bool) -> dict:
    """
    Toggle TUN mode preference.

    Args:
        enabled: True to enable, False to disable

    Returns:
        {
            'success': bool,
            'enabled': bool,
            'hasPrivileges': bool,
            'error': str | None
        }
    """
```

**Response Format**:

```typescript
interface ToggleTUNModeResponse {
  success: boolean
  enabled: boolean
  hasPrivileges: boolean
  error?: string
}
```

**Error Cases**:

- Privileges insufficient → `success: false, error: "TUN mode requires elevated privileges. Please complete installation steps."`

---

#### `check_tun_privileges`

**Purpose**: Check if plugin has required privileges for TUN mode.

**Frontend Call**:

```typescript
const result = await serverAPI.callPluginMethod('check_tun_privileges', {})
```

**Backend Signature**:

```python
async def check_tun_privileges(self) -> dict:
    """
    Check if plugin has required privileges for TUN mode.

    Returns:
        {
            'hasPrivileges': bool,
            'error': str | None
        }
    """
```

**Response Format**:

```typescript
interface CheckPrivilegesResponse {
  hasPrivileges: boolean
  error?: string // Error message if check failed
}
```

---

#### `get_tun_mode_status`

**Purpose**: Get TUN mode preference and status.

**Frontend Call**:

```typescript
const result = await serverAPI.callPluginMethod('get_tun_mode_status', {})
```

**Backend Signature**:

```python
async def get_tun_mode_status(self) -> dict:
    """
    Get TUN mode preference and status.

    Returns:
        {
            'enabled': bool,
            'hasPrivileges': bool,
            'tunInterface': str | None,
            'isActive': bool
        }
    """
```

**Response Format**:

```typescript
interface TUNModeStatusResponse {
  enabled: boolean
  hasPrivileges: boolean
  tunInterface?: string // e.g., 'tun0'
  isActive: boolean // Whether TUN is currently active
}
```

---

### 4. System Proxy (Auto-managed with TUN Mode)

When TUN mode connects, the backend automatically enables System Proxy via gsettings (GNOME/GTK) or kwriteconfig5 (KDE). SOCKS 127.0.0.1:10808, HTTP 127.0.0.1:10809. On disconnect, System Proxy is automatically cleared. No frontend action required for TUN mode.

Optional API for manual control when connecting without TUN mode:

- `toggle_system_proxy(enabled: bool)` — enable/disable system proxy (requires active connection)
- `get_system_proxy_status()` — returns `{ enabled, isActive, socksPort?, httpPort?, address? }`

---

### 5. Kill Switch Management

#### `toggle_kill_switch`

**Purpose**: Enable or disable kill switch preference.

**Frontend Call**:

```typescript
const result = await serverAPI.callPluginMethod('toggle_kill_switch', {
  enabled: boolean,
})
```

**Backend Signature**:

```python
async def toggle_kill_switch(self, enabled: bool) -> dict:
    """
    Toggle kill switch preference.

    Args:
        enabled: True to enable, False to disable

    Returns:
        {
            'success': bool,
            'enabled': bool
        }
    """
```

**Response Format**:

```typescript
interface ToggleKillSwitchResponse {
  success: boolean
  enabled: boolean
}
```

---

#### `get_kill_switch_status`

**Purpose**: Get kill switch preference and active state.

**Frontend Call**:

```typescript
const result = await serverAPI.callPluginMethod('get_kill_switch_status', {})
```

**Backend Signature**:

```python
async def get_kill_switch_status(self) -> dict:
    """
    Get kill switch preference and active state.

    Returns:
        {
            'enabled': bool,
            'isActive': bool,  # Whether kill switch is currently blocking
            'activatedAt': int | None  # When kill switch was activated
        }
    """
```

**Response Format**:

```typescript
interface KillSwitchStatusResponse {
  enabled: boolean
  isActive: boolean
  activatedAt?: number // Unix timestamp
}
```

---

#### `deactivate_kill_switch`

**Purpose**: Manually deactivate kill switch (when user reconnects or disables).

**Frontend Call**:

```typescript
const result = await serverAPI.callPluginMethod('deactivate_kill_switch', {})
```

**Backend Signature**:

```python
async def deactivate_kill_switch(self) -> dict:
    """
    Manually deactivate kill switch.

    Returns:
        {
            'success': bool,
            'error': str | None
        }
    """
```

**Response Format**:

```typescript
interface DeactivateKillSwitchResponse {
  success: boolean
  error?: string
}
```

---

## Error Handling

### Standard Error Response Format

All methods return a consistent error format:

```typescript
interface ErrorResponse {
  success: false
  error: string // Human-readable error message
  errorCode?: string // Optional error code for programmatic handling
}
```

### Error Codes

- `NO_CONFIG`: No VLESS config stored
- `NOT_CONNECTED`: System proxy requires active connection (for manual toggle_system_proxy)
- `INVALID_CONFIG`: VLESS config is invalid
- `INVALID_URL`: Invalid VLESS URL format
- `NETWORK_ERROR`: Network operation failed
- `PRIVILEGES_INSUFFICIENT`: Required privileges not available
- `PROCESS_FAILED`: xray-core process failed
- `IPTABLES_FAILED`: iptables operation failed
- `UNKNOWN_ERROR`: Unexpected error occurred

---

## Type Definitions

### Complete TypeScript Types

```typescript
// VLESS Config
interface VLESSConfig {
  sourceUrl: string
  configType: 'single' | 'subscription'
  uuid: string
  address: string
  port: number
  flow?: string
  encryption?: string
  network?: string
  security?: string
  realityConfig?: {
    publicKey: string
    shortId: string
    serverName: string
    fingerprint?: string
  }
  name?: string
  importedAt: number
  lastValidatedAt?: number
  isValid: boolean
  validationError?: string
}

// Connection Status
type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error' | 'blocked'

// API Response Types (as defined above)
```

---

## Usage Examples

### Example: Import Config

```typescript
// Frontend
try {
  const result = await serverAPI.callPluginMethod('import_vless_config', {
    url: 'vless://uuid@example.com:443?security=reality#MyServer',
  })

  if (result.success) {
    console.log('Config imported:', result.config)
  } else {
    console.error('Import failed:', result.error)
  }
} catch (error) {
  console.error('API call failed:', error)
}
```

### Example: Toggle Connection

```typescript
// Frontend
const result = await serverAPI.callPluginMethod('toggle_connection', {
  enable: true,
})

if (result.success) {
  console.log('Connection status:', result.status)
} else {
  console.error('Toggle failed:', result.error)
}
```

### Example: Check TUN Privileges

```typescript
// Frontend
const result = await serverAPI.callPluginMethod('check_tun_privileges', {})

if (result.hasPrivileges) {
  // Enable TUN mode toggle
} else {
  // Show message about needing privileges
}
```

---

## Backend Implementation Notes

### Method Naming Convention

- Use snake_case for Python method names
- Match frontend camelCase in callPluginMethod calls

### Async/Await

- All backend methods are async
- Use `asyncio` for non-blocking operations
- Handle timeouts appropriately

### Error Handling

- Always return dict with 'success' and 'error' fields
- Log errors for debugging
- Provide user-friendly error messages

### Settings Persistence

- Use SettingsManager for all persistent data
- Never use direct filesystem access
- Handle SettingsManager errors gracefully

---

## Testing

### Unit Tests

- Test each method with valid inputs
- Test error cases (invalid config, no privileges, etc.)
- Mock external dependencies (xray-core, iptables)

### Integration Tests

- Test full flows (import → connect → disconnect)
- Test error recovery
- Test state persistence

### Frontend Tests

- Mock ServerAPI calls
- Test UI updates based on responses
- Test error handling in UI
