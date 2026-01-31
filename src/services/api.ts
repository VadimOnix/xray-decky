/**
 * API Service - Backend calls using @decky/api (new API)
 *
 * Uses callable() for typed backend method calls.
 * https://wiki.deckbrew.xyz/en/plugin-dev/backend-frontend-communication
 */

import { callable } from '@decky/api'

// #region agent log - debug callable
console.log('[api.ts] Module loaded, callable:', typeof callable, callable)
// #endregion

// Type definitions
export interface VLESSConfig {
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

export interface ImportConfigResponse {
  success: boolean
  config?: VLESSConfig
  error?: string
}

export interface GetConfigResponse {
  config?: VLESSConfig
  exists: boolean
}

export interface ValidateConfigResponse {
  isValid: boolean
  error?: string
}

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error' | 'blocked'

export interface ConnectionStatusResponse {
  status: ConnectionStatus
  connectedAt?: number
  errorMessage?: string
  processId?: number
  uptime?: number
}

export interface ToggleConnectionResponse {
  success: boolean
  status: ConnectionStatus
  error?: string
  processId?: number
}

export interface ToggleTUNModeResponse {
  success: boolean
  enabled: boolean
  hasPrivileges: boolean
  error?: string
}

export interface CheckPrivilegesResponse {
  hasPrivileges: boolean
  error?: string
}

export interface TUNModeStatusResponse {
  enabled: boolean
  hasPrivileges: boolean
  tunInterface?: string
  isActive: boolean
}

export interface ToggleKillSwitchResponse {
  success: boolean
  enabled: boolean
}

export interface KillSwitchStatusResponse {
  enabled: boolean
  isActive: boolean
  activatedAt?: number
}

export interface DeactivateKillSwitchResponse {
  success: boolean
  error?: string
}

export interface ImportServerUrlResponse {
  baseUrl: string
  path: string
}

// Backend method handles using callable (new API)
// callable<[arg types], returnType>("method_name")

export const importVLESSConfig = callable<[url: string], ImportConfigResponse>('import_vless_config')

export const getVLESSConfig = callable<[], GetConfigResponse>('get_vless_config')

export const validateVLESSConfig = callable<[], ValidateConfigResponse>('validate_vless_config')

export const toggleConnection = callable<[enable: boolean], ToggleConnectionResponse>('toggle_connection')

export const getConnectionStatus = callable<[], ConnectionStatusResponse>('get_connection_status')

export const toggleTUNMode = callable<[enabled: boolean], ToggleTUNModeResponse>('toggle_tun_mode')

export const checkTUNPrivileges = callable<[], CheckPrivilegesResponse>('check_tun_privileges')

export const getTUNModeStatus = callable<[], TUNModeStatusResponse>('get_tun_mode_status')

export const toggleKillSwitch = callable<[enabled: boolean], ToggleKillSwitchResponse>('toggle_kill_switch')

export const getKillSwitchStatus = callable<[], KillSwitchStatusResponse>('get_kill_switch_status')

export const deactivateKillSwitch = callable<[], DeactivateKillSwitchResponse>('deactivate_kill_switch')

// #region agent log - wrapped callable with logging
const _getImportServerUrl = callable<[], ImportServerUrlResponse>('get_import_server_url')
console.log('[api.ts] _getImportServerUrl callable created:', typeof _getImportServerUrl, _getImportServerUrl)

export const getImportServerUrl = async (): Promise<ImportServerUrlResponse> => {
  console.log('[api.ts] getImportServerUrl() called, invoking callable...')
  try {
    const result = await _getImportServerUrl()
    console.log('[api.ts] getImportServerUrl() result:', result)
    return result
  } catch (err) {
    console.error('[api.ts] getImportServerUrl() error:', err)
    throw err
  }
}
// #endregion
