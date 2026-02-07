import type { ConnectionStatus } from '../services/api'

export type UILayout = 'setup' | 'configured'

export type HelpTopic =
  | 'setup.qr_import'
  | 'setup.lan_address'
  | 'setup.vless_link'
  | 'configured.status'
  | 'configured.reset'
  | 'options.tun_mode'
  | 'options.kill_switch'

export interface ConnectionConfigSummary {
  exists: boolean
  displayName?: string
  endpoint?: string
  isValid: boolean
  validationError?: string
  source?: string
}

export interface ConnectionState {
  status: ConnectionStatus
  message?: string
  connectedAt?: number
  uptime?: number
}

export interface OptionsState {
  tunEnabled: boolean
  tunHasPrivileges: boolean
  tunActive: boolean
  killSwitchEnabled: boolean
  killSwitchActive: boolean
  killSwitchActivatedAt?: number
}

export interface PluginPanelState {
  layout: UILayout
  configSummary: ConnectionConfigSummary
  connection: ConnectionState
  options: OptionsState
  isLoading: boolean
  lastUpdatedAt?: number
}
