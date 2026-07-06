/**
 * API Service - Backend calls using @decky/api (new API)
 *
 * Uses callable() for typed backend method calls.
 * https://wiki.deckbrew.xyz/en/plugin-dev/backend-frontend-communication
 */

import { callable } from '@decky/api';

// Type definitions
export interface VLESSConfig {
  sourceUrl: string;
  configType: 'single' | 'subscription';
  uuid: string;
  address: string;
  port: number;
  flow?: string;
  encryption?: string;
  network?: string;
  security?: string;
  realityConfig?: {
    publicKey: string;
    shortId: string;
    serverName: string;
    fingerprint?: string;
  };
  name?: string;
  importedAt: number;
  lastValidatedAt?: number;
  isValid: boolean;
  validationError?: string;
}

export interface ImportConfigResponse {
  success: boolean;
  config?: VLESSConfig;
  error?: string;
}

export interface ResetConfigResponse {
  success: boolean;
  error?: string;
}

export interface GetConfigResponse {
  config?: VLESSConfig;
  exists: boolean;
}

export interface ValidateConfigResponse {
  isValid: boolean;
  error?: string;
}

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error' | 'blocked';

export interface ConnectionStatusResponse {
  status: ConnectionStatus;
  connectedAt?: number;
  errorMessage?: string;
  processId?: number;
  uptime?: number;
}

export interface ToggleConnectionResponse {
  success: boolean;
  status: ConnectionStatus;
  error?: string;
  processId?: number;
}

export interface ToggleTUNModeResponse {
  success: boolean;
  enabled: boolean;
  hasPrivileges: boolean;
  error?: string;
}

export interface CheckPrivilegesResponse {
  hasPrivileges: boolean;
  error?: string;
}

export interface TUNModeStatusResponse {
  enabled: boolean;
  hasPrivileges: boolean;
  tunInterface?: string;
  isActive: boolean;
}

export interface ToggleKillSwitchResponse {
  success: boolean;
  enabled: boolean;
}

export interface KillSwitchStatusResponse {
  enabled: boolean;
  isActive: boolean;
  activatedAt?: number;
}

export interface DeactivateKillSwitchResponse {
  success: boolean;
  error?: string;
}

export interface ToggleSystemProxyResponse {
  success: boolean;
  enabled: boolean;
  error?: string;
  socksPort?: number | null;
  httpPort?: number | null;
}

export interface SystemProxyStatusResponse {
  enabled: boolean;
  isActive: boolean;
  socksPort?: number | null;
  httpPort?: number | null;
  address?: string | null;
  error?: string;
}

export interface ImportServerUrlResponse {
  baseUrl: string;
  path: string;
}

export interface AdminPanelUrlResponse {
  baseUrl: string;
  path: string;
  token: string;
  allowLan?: boolean;
}

export interface SetLanAccessResponse {
  success: boolean;
  allowLan?: boolean;
  serverRunning?: boolean;
  error?: string;
}

export interface HandleResumeResponse {
  success: boolean;
  checked?: boolean;
  routeRestored?: boolean;
  error?: string;
}

// Backend method handles using callable (new API)
// callable<[arg types], returnType>("method_name")

export const importVLESSConfig = callable<[url: string], ImportConfigResponse>(
  'import_vless_config'
);

export const getVLESSConfig = callable<[], GetConfigResponse>('get_vless_config');

export const resetVLESSConfig = callable<[], ResetConfigResponse>('reset_vless_config');

export const validateVLESSConfig = callable<[], ValidateConfigResponse>('validate_vless_config');

export const toggleConnection = callable<[enable: boolean], ToggleConnectionResponse>(
  'toggle_connection'
);

export const getConnectionStatus = callable<[], ConnectionStatusResponse>('get_connection_status');

export const toggleTUNMode = callable<[enabled: boolean], ToggleTUNModeResponse>('toggle_tun_mode');

export const checkTUNPrivileges = callable<[], CheckPrivilegesResponse>('check_tun_privileges');

export const getTUNModeStatus = callable<[], TUNModeStatusResponse>('get_tun_mode_status');

export const toggleKillSwitch = callable<[enabled: boolean], ToggleKillSwitchResponse>(
  'toggle_kill_switch'
);

export const getKillSwitchStatus = callable<[], KillSwitchStatusResponse>('get_kill_switch_status');

export const deactivateKillSwitch = callable<[], DeactivateKillSwitchResponse>(
  'deactivate_kill_switch'
);

export const toggleSystemProxy = callable<[enabled: boolean], ToggleSystemProxyResponse>(
  'toggle_system_proxy'
);

export const getSystemProxyStatus = callable<[], SystemProxyStatusResponse>(
  'get_system_proxy_status'
);

export const getImportServerUrl = callable<[], ImportServerUrlResponse>('get_import_server_url');
export const getAdminPanelUrl = callable<[], AdminPanelUrlResponse>('get_admin_panel_url');

export const setLanAccess = callable<[enabled: boolean], SetLanAccessResponse>('set_lan_access');
export const handleResume = callable<[], HandleResumeResponse>('handle_resume');

export interface ServerProfile {
  id: string;
  protocol?: string;
  name?: string;
  address?: string;
  port?: number;
  network?: string;
  security?: string;
  latencyMs?: number | null;
  latencyTestedAt?: number;
}

export interface GetProfilesResponse {
  success: boolean;
  activeId?: string | null;
  profiles: ServerProfile[];
  error?: string;
}

export interface SetActiveProfileResponse {
  success: boolean;
  activeId?: string;
  reconnected?: boolean;
  error?: string;
}

export interface TestLatencyResponse {
  success: boolean;
  results?: Record<string, number | null>;
  error?: string;
}

export interface TrafficStatsResponse {
  success: boolean;
  available: boolean;
  uplink: number;
  downlink: number;
  uplinkSpeed: number;
  downlinkSpeed: number;
  error?: string;
}

export const getProfiles = callable<[], GetProfilesResponse>('get_profiles');
export const setActiveProfile = callable<[profileId: string], SetActiveProfileResponse>(
  'set_active_profile'
);
export const testProfilesLatency = callable<[], TestLatencyResponse>('test_profiles_latency');
export const getTrafficStats = callable<[], TrafficStatsResponse>('get_traffic_stats');
