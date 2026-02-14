import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { addEventListener, removeEventListener } from '@decky/api'
import { useQuickAccessVisible } from '@decky/ui'
import {
  checkTUNPrivileges,
  deactivateKillSwitch,
  getConnectionStatus,
  getKillSwitchStatus,
  getTUNModeStatus,
  getVLESSConfig,
  importVLESSConfig,
  resetVLESSConfig,
  toggleConnection,
  toggleKillSwitch,
  toggleTUNMode,
  type CheckPrivilegesResponse,
  type DeactivateKillSwitchResponse,
  type GetConfigResponse,
  type ImportConfigResponse,
  type ToggleConnectionResponse,
  type ToggleKillSwitchResponse,
  type ToggleTUNModeResponse,
  type VLESSConfig,
} from '../services/api'
import { getValidationErrorMessage, validateVLESSURL } from '../utils/validation'
import type { ConnectionConfigSummary, ConnectionState, OptionsState, PluginPanelState, UILayout } from '../types/ui'

const VLESS_CONFIG_UPDATED_EVENT = 'vless_config_updated'
const POLL_INTERVAL_MS = 2000

const emptyOptionsState: OptionsState = {
  tunEnabled: false,
  tunHasPrivileges: false,
  tunActive: false,
  killSwitchEnabled: false,
  killSwitchActive: false,
}

const emptyConnectionState: ConnectionState = {
  status: 'disconnected',
}

const emptyConfigSummary: ConnectionConfigSummary = {
  exists: false,
  isValid: false,
}

const deriveConfigSummary = (config: VLESSConfig | null, exists: boolean): ConnectionConfigSummary => {
  if (!exists || !config) {
    return { ...emptyConfigSummary }
  }

  const endpoint = config.address && config.port ? `${config.address}:${config.port}` : undefined
  const displayName = config.name || undefined
  const source = config.configType === 'subscription' ? 'Subscription' : 'Imported link'

  return {
    exists: true,
    displayName,
    endpoint,
    isValid: config.isValid,
    validationError: config.validationError,
    source,
  }
}

export interface PluginPanelActions {
  refresh: () => Promise<void>
  saveConfig: (url: string) => Promise<ImportConfigResponse>
  resetConfig: () => Promise<{ success: boolean; error?: string }>
  toggleConnection: (enable: boolean) => Promise<ToggleConnectionResponse>
  toggleTUNMode: (enabled: boolean) => Promise<ToggleTUNModeResponse>
  toggleKillSwitch: (enabled: boolean) => Promise<ToggleKillSwitchResponse>
  deactivateKillSwitch: () => Promise<DeactivateKillSwitchResponse>
  checkTUNPrivileges: () => Promise<CheckPrivilegesResponse>
}

export function usePluginPanelState(): PluginPanelState & PluginPanelActions {
  const [config, setConfig] = useState<VLESSConfig | null>(null)
  const [configExists, setConfigExists] = useState(false)
  const [connection, setConnection] = useState<ConnectionState>(emptyConnectionState)
  const [options, setOptions] = useState<OptionsState>(emptyOptionsState)
  const [isLoading, setIsLoading] = useState(true)
  const [lastUpdatedAt, setLastUpdatedAt] = useState<number | undefined>(undefined)
  const isMountedRef = useRef(true)
  const isVisible = useQuickAccessVisible()

  useEffect(() => {
    return () => {
      isMountedRef.current = false
    }
  }, [])

  const applyConfigResult = useCallback((result: GetConfigResponse) => {
    const exists = Boolean(result.exists && result.config)
    setConfigExists(exists)
    setConfig(exists ? result.config ?? null : null)
  }, [])

  const refresh = useCallback(async () => {
    try {
      const [configResult, connectionResult, tunResult, killSwitchResult] = await Promise.all([
        getVLESSConfig(),
        getConnectionStatus(),
        getTUNModeStatus(),
        getKillSwitchStatus(),
      ])

      if (!isMountedRef.current) return

      applyConfigResult(configResult)
      setConnection({
        status: connectionResult.status,
        message: connectionResult.errorMessage,
        connectedAt: connectionResult.connectedAt,
        uptime: connectionResult.uptime,
      })
      setOptions({
        tunEnabled: tunResult.enabled === true,
        tunHasPrivileges: tunResult.hasPrivileges ?? false,
        tunActive: tunResult.isActive,
        killSwitchEnabled: killSwitchResult.enabled,
        killSwitchActive: killSwitchResult.isActive,
        killSwitchActivatedAt: killSwitchResult.activatedAt,
      })
      setLastUpdatedAt(Date.now())
    } catch (error) {
      if (!isMountedRef.current) return
      console.error('Failed to refresh plugin panel state:', error)
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false)
      }
    }
  }, [applyConfigResult])

  useEffect(() => {
    if (!isVisible) return
    void refresh()

    const interval = setInterval(() => {
      void refresh()
    }, POLL_INTERVAL_MS)

    return () => clearInterval(interval)
  }, [isVisible, refresh])

  useEffect(() => {
    const listener = addEventListener(VLESS_CONFIG_UPDATED_EVENT, () => {
      void refresh()
    })

    return () => {
      removeEventListener(VLESS_CONFIG_UPDATED_EVENT, listener)
    }
  }, [refresh])

  const saveConfig = useCallback(async (url: string): Promise<ImportConfigResponse> => {
    const trimmed = url.trim()
    if (!trimmed) {
      return { success: false, error: 'Please enter a VLESS URL' }
    }
    if (!validateVLESSURL(trimmed)) {
      return {
        success: false,
        error: 'Invalid VLESS URL format. Please check the URL and try again.',
      }
    }

    const result = await importVLESSConfig(trimmed)
    if (result.success && result.config) {
      setConfigExists(true)
      setConfig(result.config)
    }

    if (!result.success && result.error) {
      return {
        ...result,
        error: getValidationErrorMessage(result.error),
      }
    }

    return result
  }, [])

  const resetConfig = useCallback(async () => {
    const result = await resetVLESSConfig()
    if (result.success) {
      setConfigExists(false)
      setConfig(null)
    }
    void refresh()
    return result
  }, [refresh])

  const handleToggleConnection = useCallback(
    async (enable: boolean): Promise<ToggleConnectionResponse> => {
      const result = await toggleConnection(enable)
      void refresh()
      return result
    },
    [refresh]
  )

  const handleToggleTUNMode = useCallback(
    async (enabled: boolean): Promise<ToggleTUNModeResponse> => {
      const result = await toggleTUNMode(enabled)
      void refresh()
      return result
    },
    [refresh]
  )

  const handleCheckPrivileges = useCallback(async (): Promise<CheckPrivilegesResponse> => {
    const result = await checkTUNPrivileges()
    void refresh()
    return result
  }, [refresh])

  const handleToggleKillSwitch = useCallback(
    async (enabled: boolean): Promise<ToggleKillSwitchResponse> => {
      const result = await toggleKillSwitch(enabled)
      void refresh()
      return result
    },
    [refresh]
  )

  const handleDeactivateKillSwitch = useCallback(async (): Promise<DeactivateKillSwitchResponse> => {
    const result = await deactivateKillSwitch()
    void refresh()
    return result
  }, [refresh])

  const layout: UILayout = configExists ? 'configured' : 'setup'
  const configSummary = useMemo(() => deriveConfigSummary(config, configExists), [config, configExists])

  return {
    layout,
    configSummary,
    connection,
    options,
    isLoading,
    lastUpdatedAt,
    refresh,
    saveConfig,
    resetConfig,
    toggleConnection: handleToggleConnection,
    toggleTUNMode: handleToggleTUNMode,
    toggleKillSwitch: handleToggleKillSwitch,
    deactivateKillSwitch: handleDeactivateKillSwitch,
    checkTUNPrivileges: handleCheckPrivileges,
  }
}
