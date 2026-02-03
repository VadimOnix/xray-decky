# Data Model: Xray Reality VLESS Decky Plugin

**Date**: 2026-01-26  
**Feature**: 001-xray-vless-decky  
**Status**: Phase 1 Design

## Overview

This document defines the data entities, their structure, relationships, and validation rules for the Xray Reality VLESS Decky Plugin.

---

## Entities

### 1. VLESS Configuration

**Purpose**: Stores user's VLESS proxy configuration obtained via URL.

**Storage**: SettingsManager (JSON file via `DECKY_PLUGIN_SETTINGS_DIR`)

**Structure**:

```typescript
interface VLESSConfig {
  // Source information
  sourceUrl: string // Original URL (single node or subscription)
  configType: 'single' | 'subscription' // Type of config source

  // Parsed configuration
  uuid: string // VLESS UUID (validated format)
  address: string // Server address (hostname or IP)
  port: number // Server port (1-65535)
  flow?: string // Optional flow parameter
  encryption?: string // Encryption method
  network?: string // Network type (tcp, ws, etc.)
  security?: string // Security type (reality, tls, etc.)

  // Reality-specific fields (if applicable)
  // Note: xray-core CLIENT config uses publicKey (server's public key), serverName, shortId, fingerprint.
  // NEVER use privateKey, dest, xver—those are server-side only.
  realityConfig?: {
    publicKey: string // Server public key (required for client)
    shortId: string
    serverName: string
    fingerprint?: string
  }

  // Metadata
  name?: string // Display name (from URL fragment)
  importedAt: number // Timestamp (Unix epoch)
  lastValidatedAt?: number // Last validation timestamp
  isValid: boolean // Current validation status
  validationError?: string // Error message if invalid
}
```

**Validation Rules**:

- `sourceUrl`: Must match VLESS URL pattern or be valid base64 subscription
- `uuid`: Must be valid UUID v4 format
- `address`: Must be valid hostname or IP address
- `port`: Must be integer between 1 and 65535
- `configType`: Must be 'single' or 'subscription'
- All required fields must be present for `isValid: true`

**State Transitions**:

```
[Empty] → [Imported] → [Validated] → [Active]
                ↓           ↓
            [Invalid]  [Validation Error]
```

**Relationships**:

- One-to-one with ConnectionState (when active)
- Referenced by ConnectionManager for establishing proxy

---

### 2. Connection State

**Purpose**: Tracks current proxy connection status and lifecycle.

**Storage**: In-memory (managed by ConnectionManager), persisted preferences via SettingsManager

**Structure**:

```typescript
interface ConnectionState {
  // Current status
  status: 'disconnected' | 'connecting' | 'connected' | 'error' | 'blocked'

  // Connection details
  connectedAt?: number // Timestamp when connected
  disconnectedAt?: number // Timestamp when disconnected
  errorMessage?: string // Error message if status is 'error'
  errorCode?: string // Error code for categorization

  // Process information
  xrayProcessId?: number // xray-core process PID
  xrayConfigPath?: string // Path to active xray config file

  // Active configuration
  activeConfig?: VLESSConfig // Currently active VLESS config (if connected)

  // Connection metrics (optional)
  bytesSent?: number // Total bytes sent
  bytesReceived?: number // Total bytes received
  uptime?: number // Connection uptime in seconds
}
```

**Validation Rules**:

- `status`: Must be one of the defined status values
- `xrayProcessId`: Must be valid process ID if status is 'connected' or 'connecting'
- `activeConfig`: Must be valid VLESSConfig if status is 'connected'
- `errorMessage`: Required if status is 'error'

**State Transitions**:

```
[disconnected] → [connecting] → [connected]
                      ↓              ↓
                  [error]      [disconnected] (user toggle)
                                    ↓
                              [blocked] (kill switch active)
```

**Relationships**:

- References VLESSConfig (when active)
- Managed by ConnectionManager
- Monitored by KillSwitchManager (for unexpected disconnects)

---

### 3. TUN Mode Preference

**Purpose**: Stores user's preference for system-wide tunneling.

**Storage**: SettingsManager (JSON file)

**Structure**:

```typescript
interface TUNModePreference {
  enabled: boolean // User's preference (on/off)
  lastEnabledAt?: number // Timestamp when last enabled
  lastDisabledAt?: number // Timestamp when last disabled

  // Privilege status
  hasPrivileges: boolean // Whether plugin has required privileges
  privilegeCheckAt?: number // Last privilege check timestamp
  privilegeError?: string // Error message if privileges insufficient

  // TUN interface information (when active)
  tunInterface?: string // TUN interface name (e.g., 'tun0')
  tunCreatedAt?: number // When TUN interface was created
}
```

**Validation Rules**:

- `enabled`: Boolean value
- `hasPrivileges`: Must be true if `enabled` is true
- `tunInterface`: Required if `enabled` is true and connection is active

**State Transitions**:

```
[disabled] → [checking privileges] → [enabled]
                 ↓
            [insufficient privileges] → [disabled]
```

**Relationships**:

- Used by ConnectionManager when establishing connection
- Checked by TUNManager for privilege validation

---

### 4. Kill Switch Preference

**Purpose**: Stores user's preference for kill switch functionality.

**Storage**: SettingsManager (JSON file)

**Structure**:

```typescript
interface KillSwitchPreference {
  enabled: boolean // User's preference (off by default)
  lastEnabledAt?: number // Timestamp when last enabled
  lastDisabledAt?: number // Timestamp when last disabled

  // Active state
  isActive: boolean // Whether kill switch is currently blocking traffic
  activatedAt?: number // When kill switch was activated (unexpected disconnect)
  deactivatedAt?: number // When kill switch was deactivated

  // Blocking information
  blockedUntil?: number // Timestamp until which traffic is blocked
  iptablesRulesApplied?: boolean // Whether iptables rules are active
  ruleIds?: string[] // iptables rule identifiers for cleanup
}
```

**Validation Rules**:

- `enabled`: Boolean value (default: false)
- `isActive`: Can only be true if `enabled` is true
- `iptablesRulesApplied`: Must be true if `isActive` is true

**State Transitions**:

```
[disabled] → [enabled] → [active] (on unexpected disconnect)
                            ↓
                    [deactivated] (user reconnects or disables)
```

**Relationships**:

- Monitored by KillSwitchManager
- Activated by ConnectionManager on unexpected disconnect
- Uses iptables rules for traffic blocking

---

## Settings Storage Structure

**File**: `settings.json` (via SettingsManager)

**Location**: `DECKY_PLUGIN_SETTINGS_DIR` (provided by Decky Loader)

**Structure**:

```json
{
  "vlessConfig": {
    "sourceUrl": "vless://...",
    "configType": "single",
    "uuid": "...",
    "address": "...",
    "port": 443,
    "isValid": true,
    "importedAt": 1706284800
  },
  "tunMode": {
    "enabled": false,
    "hasPrivileges": false
  },
  "killSwitch": {
    "enabled": false,
    "isActive": false
  },
  "connectionState": {
    "status": "disconnected"
  }
}
```

**Persistence Rules**:

- All user preferences persisted across plugin restarts
- Connection state (status) persisted for UI restoration
- Active connection details (process ID, config path) not persisted (recreated on restart)
- Timestamps stored as Unix epoch (seconds)

---

## Validation Rules Summary

### VLESS URL Validation

1. Must match pattern: `vless://uuid@host:port?params#name`
2. UUID must be valid UUID v4 format
3. Host must be valid hostname or IP address
4. Port must be integer 1-65535
5. Parameters must be valid URL-encoded key-value pairs
6. Subscription URLs must be valid base64-encoded JSON array

### Configuration Validation

1. All required fields present
2. UUID format valid
3. Address resolvable (hostname or IP)
4. Port in valid range
5. Reality config complete if security type is 'reality'

### State Consistency

1. Connection state must match actual xray-core process status
2. TUN mode can only be enabled if privileges available
3. Kill switch can only be active if enabled
4. Active config must be valid when connection is 'connected'

---

## Data Flow

### Import Flow

```
User Input (VLESS URL)
  → Validation (regex + format check)
  → Parsing (extract components)
  → Storage (SettingsManager)
  → UI Update (show success/error)
```

### Connection Flow

```
User Toggle On
  → Load VLESS Config
  → Validate Config
  → Check TUN Mode Preference
  → Check Privileges (if TUN)
  → Generate xray-core Config
  → Start xray-core Process
  → Update Connection State
  → Monitor Connection (for unexpected disconnect)
```

### Kill Switch Flow

```
Unexpected Disconnect Detected
  → Check Kill Switch Preference (enabled?)
  → Apply iptables Rules (block all traffic)
  → Update Kill Switch State (isActive: true)
  → Show Notification (toast)
  → Update UI (show blocked message)
```

---

## Error Handling

### Validation Errors

- Invalid URL format → Clear error message, no storage
- Invalid UUID → Clear error message, no storage
- Invalid port → Clear error message, no storage
- Missing required fields → Clear error message, mark as invalid

### Connection Errors

- Config invalid → Error status, show error message
- Privileges insufficient → Error status, guide user to fix
- xray-core process failed → Error status, show error message
- Network error → Error status, allow retry

### Kill Switch Errors

- iptables rules failed → Log error, show warning (kill switch may not work)
- Cleanup failed → Log error, attempt manual cleanup on next start

---

## Migration and Compatibility

### Future Considerations

- Support for multiple VLESS configs (subscription with multiple nodes)
- Config versioning (if xray-core config format changes)
- Settings migration (if data model changes)

### Backward Compatibility

- Default values for new fields
- Graceful handling of missing fields
- Validation before use (never assume data is valid)
