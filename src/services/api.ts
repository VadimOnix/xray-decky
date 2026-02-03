/**
 * API Service - Backend calls using @decky/api (new API)
 *
 * Uses callable() for typed backend method calls.
 * https://wiki.deckbrew.xyz/en/plugin-dev/backend-frontend-communication
 */

import { callable } from '@decky/api'

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

export const getImportServerUrl = callable<[], ImportServerUrlResponse>('get_import_server_url')
