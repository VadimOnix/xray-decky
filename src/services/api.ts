/**
 * API Service - Wrapper for ServerAPI calls
 *
 * Provides typed methods for all backend API calls.
 */

import { ServerAPI } from 'decky-frontend-lib'

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

/**
 * API service class for backend communication
 */
export class APIService {
  constructor(private serverAPI: ServerAPI) {}

  /**
   * Import VLESS configuration from URL
   */
  async importVLESSConfig(url: string): Promise<ImportConfigResponse> {
    const response = await this.serverAPI.callPluginMethod<{ url: string }, ImportConfigResponse>(
      'import_vless_config',
      { url }
    )
    return response.result as ImportConfigResponse
  }

  /**
   * Get stored VLESS configuration
   */
  async getVLESSConfig(): Promise<GetConfigResponse> {
    const response = await this.serverAPI.callPluginMethod<{}, GetConfigResponse>('get_vless_config', {})
    return response.result as GetConfigResponse
  }

  /**
   * Validate stored VLESS configuration
   */
  async validateVLESSConfig(): Promise<ValidateConfigResponse> {
    const response = await this.serverAPI.callPluginMethod<{}, ValidateConfigResponse>('validate_vless_config', {})
    return response.result as ValidateConfigResponse
  }

  /**
   * Toggle connection on/off
   */
  async toggleConnection(enable: boolean): Promise<ToggleConnectionResponse> {
    const response = await this.serverAPI.callPluginMethod<{ enable: boolean }, ToggleConnectionResponse>(
      'toggle_connection',
      { enable }
    )
    return response.result as ToggleConnectionResponse
  }

  /**
   * Get current connection status
   */
  async getConnectionStatus(): Promise<ConnectionStatusResponse> {
    const response = await this.serverAPI.callPluginMethod<{}, ConnectionStatusResponse>('get_connection_status', {})
    return response.result as ConnectionStatusResponse
  }

  /**
   * Toggle TUN mode
   */
  async toggleTUNMode(enabled: boolean): Promise<ToggleTUNModeResponse> {
    const response = await this.serverAPI.callPluginMethod<{ enabled: boolean }, ToggleTUNModeResponse>(
      'toggle_tun_mode',
      { enabled }
    )
    return response.result as ToggleTUNModeResponse
  }

  /**
   * Check TUN privileges
   */
  async checkTUNPrivileges(): Promise<CheckPrivilegesResponse> {
    const response = await this.serverAPI.callPluginMethod<{}, CheckPrivilegesResponse>('check_tun_privileges', {})
    return response.result as CheckPrivilegesResponse
  }

  /**
   * Get TUN mode status
   */
  async getTUNModeStatus(): Promise<TUNModeStatusResponse> {
    const response = await this.serverAPI.callPluginMethod<{}, TUNModeStatusResponse>('get_tun_mode_status', {})
    return response.result as TUNModeStatusResponse
  }

  /**
   * Toggle kill switch
   */
  async toggleKillSwitch(enabled: boolean): Promise<ToggleKillSwitchResponse> {
    const response = await this.serverAPI.callPluginMethod<{ enabled: boolean }, ToggleKillSwitchResponse>(
      'toggle_kill_switch',
      { enabled }
    )
    return response.result as ToggleKillSwitchResponse
  }

  /**
   * Get kill switch status
   */
  async getKillSwitchStatus(): Promise<KillSwitchStatusResponse> {
    const response = await this.serverAPI.callPluginMethod<{}, KillSwitchStatusResponse>('get_kill_switch_status', {})
    return response.result as KillSwitchStatusResponse
  }

  /**
   * Deactivate kill switch
   */
  async deactivateKillSwitch(): Promise<DeactivateKillSwitchResponse> {
    const response = await this.serverAPI.callPluginMethod<{}, DeactivateKillSwitchResponse>(
      'deactivate_kill_switch',
      {}
    )
    return response.result as DeactivateKillSwitchResponse
  }
}
