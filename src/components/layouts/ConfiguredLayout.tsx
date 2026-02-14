import type { CSSProperties } from 'react'
import { FC, useCallback, useEffect, useState } from 'react'
import { Focusable } from '@decky/ui'
import { FaPlug, FaInfoCircle, FaSlidersH } from 'react-icons/fa'
import type { IconType } from 'react-icons'
import { ConfigSummaryCard } from '../ConfigSummaryCard'
import { ConnectionToggle } from '../ConnectionToggle'
import { KillSwitchToggle } from '../KillSwitchToggle'
import { ResetConfigurationButton } from '../ResetConfigurationButton'
import { StatusDisplay } from '../StatusDisplay'
import { TUNModeToggle } from '../TUNModeToggle'
import { HelpPopover } from '../ui/HelpPopover'
import { PanelSection, PanelSectionRow } from '../ui/primitives'

import type {
  CheckPrivilegesResponse,
  DeactivateKillSwitchResponse,
  ToggleConnectionResponse,
  ToggleKillSwitchResponse,
  ToggleTUNModeResponse,
} from '../../services/api'
import type { ConnectionConfigSummary, ConnectionState, OptionsState } from '../../types/ui'

const TAB_MAIN = 'main'
const TAB_CONFIG_INFO = 'config-info'
const TAB_OPTIONS = 'options'

const TAB_TITLES: Record<string, string> = {
  [TAB_MAIN]: 'Connection',
  [TAB_CONFIG_INFO]: 'Config',
  [TAB_OPTIONS]: 'Options',
}

const TAB_SIZE = 44
const FOCUS_RING_STYLE: CSSProperties = {
  boxShadow: '0 0 0 2px #66c0f4',
  borderColor: '#66c0f4',
}

const tabButtonBaseStyle: CSSProperties = {
  width: TAB_SIZE,
  height: TAB_SIZE,
  minWidth: TAB_SIZE,
  minHeight: TAB_SIZE,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  backgroundColor: '#1b2a3a',
  border: '1px solid #3a5f8f',
  borderRadius: '6px',
  color: '#c7d5e0',
  cursor: 'pointer',
  boxSizing: 'border-box',
}

interface TabButtonProps {
  icon: IconType
  isActive: boolean
  isFocused: boolean
  onSelect: () => void
  onFocus: () => void
  onBlur: () => void
}

const TabButton: FC<TabButtonProps> = ({ icon: Icon, isActive, isFocused, onSelect, onFocus, onBlur }) => (
  <Focusable
    onClick={(e: React.MouseEvent) => {
      e.preventDefault()
      onSelect()
    }}
    onActivate={() => onSelect()}
    onFocus={onFocus}
    onBlur={onBlur}
    style={{
      ...tabButtonBaseStyle,
      ...(isActive ? { borderColor: '#66c0f4', backgroundColor: '#1e3a5f' } : {}),
      ...(isFocused ? FOCUS_RING_STYLE : {}),
    }}
  >
    <Icon size={18} />
  </Focusable>
)

interface ConfiguredLayoutProps {
  configSummary: ConnectionConfigSummary
  connection: ConnectionState
  options: OptionsState
  onToggleConnection: (enable: boolean) => Promise<ToggleConnectionResponse>
  onToggleTUNMode: (enabled: boolean) => Promise<ToggleTUNModeResponse>
  onCheckTUNPrivileges: () => Promise<CheckPrivilegesResponse>
  onToggleKillSwitch: (enabled: boolean) => Promise<ToggleKillSwitchResponse>
  onDeactivateKillSwitch: () => Promise<DeactivateKillSwitchResponse>
  onResetConfig: () => Promise<{ success: boolean; error?: string }>
}

export const ConfiguredLayout: FC<ConfiguredLayoutProps> = ({
  configSummary,
  connection,
  options,
  onToggleConnection,
  onToggleTUNMode,
  onCheckTUNPrivileges,
  onToggleKillSwitch,
  onDeactivateKillSwitch,
  onResetConfig,
}) => {
  const [activeTab, setActiveTab] = useState(TAB_MAIN)
  const [focusedTabIndex, setFocusedTabIndex] = useState<number | null>(null)
  const isResetDisabled = ['connecting', 'connected', 'blocked'].includes(connection.status)

  const tabIds = [TAB_MAIN, TAB_CONFIG_INFO, TAB_OPTIONS] as const
  const goPrev = useCallback(() => {
    setActiveTab((prev) => {
      const i = tabIds.indexOf(prev as (typeof tabIds)[number])
      return tabIds[Math.max(0, i - 1)]
    })
  }, [])
  const goNext = useCallback(() => {
    setActiveTab((prev) => {
      const i = tabIds.indexOf(prev as (typeof tabIds)[number])
      return tabIds[Math.min(tabIds.length - 1, i + 1)]
    })
  }, [])

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') {
        goPrev()
        setFocusedTabIndex((prev) => Math.max(0, (prev ?? 0) - 1))
        e.preventDefault()
      } else if (e.key === 'ArrowRight') {
        goNext()
        setFocusedTabIndex((prev) => Math.min(2, (prev ?? 0) + 1))
        e.preventDefault()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [goPrev, goNext])

  const tabRowStyle: CSSProperties = {
    display: 'flex',
    flexDirection: 'row',
    gap: '8px',
    alignItems: 'center',
  }

  return (
    <PanelSection title={TAB_TITLES[activeTab] ?? 'Connection'}>
      <PanelSectionRow>
        <Focusable {...{ 'flow-children': 'right' }} style={tabRowStyle}>
          <TabButton
            icon={FaPlug}
            isActive={activeTab === TAB_MAIN}
            isFocused={focusedTabIndex === 0}
            onSelect={() => setActiveTab(TAB_MAIN)}
            onFocus={() => setFocusedTabIndex(0)}
            onBlur={() => setFocusedTabIndex(null)}
          />
          <TabButton
            icon={FaInfoCircle}
            isActive={activeTab === TAB_CONFIG_INFO}
            isFocused={focusedTabIndex === 1}
            onSelect={() => setActiveTab(TAB_CONFIG_INFO)}
            onFocus={() => setFocusedTabIndex(1)}
            onBlur={() => setFocusedTabIndex(null)}
          />
          <TabButton
            icon={FaSlidersH}
            isActive={activeTab === TAB_OPTIONS}
            isFocused={focusedTabIndex === 2}
            onSelect={() => setActiveTab(TAB_OPTIONS)}
            onFocus={() => setFocusedTabIndex(2)}
            onBlur={() => setFocusedTabIndex(null)}
          />
        </Focusable>
      </PanelSectionRow>

      {activeTab === TAB_MAIN && (
        <>
          <PanelSectionRow>
            <ConnectionToggle status={connection.status} onToggle={onToggleConnection} />
          </PanelSectionRow>
          <PanelSectionRow>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
              <span style={{ fontSize: '14px', fontWeight: 600, color: '#c7d5e0' }}>Status</span>
              <HelpPopover label="Help: status" topic="configured.status" />
            </div>
          </PanelSectionRow>
          <PanelSectionRow>
            <StatusDisplay
              status={connection.status}
              errorMessage={connection.message}
              uptime={connection.uptime}
              connectedAt={connection.connectedAt}
            />
          </PanelSectionRow>
        </>
      )}

      {activeTab === TAB_CONFIG_INFO && (
        <PanelSectionRow>
          <ConfigSummaryCard summary={configSummary} />
        </PanelSectionRow>
      )}

      {activeTab === TAB_OPTIONS && (
        <>
          <PanelSectionRow>
            <TUNModeToggle
              enabled={options.tunEnabled}
              hasPrivileges={options.tunHasPrivileges}
              isActive={options.tunActive}
              onToggle={onToggleTUNMode}
              onCheckPrivileges={onCheckTUNPrivileges}
            />
          </PanelSectionRow>
          <PanelSectionRow>
            <KillSwitchToggle
              enabled={options.killSwitchEnabled}
              isActive={options.killSwitchActive}
              activatedAt={options.killSwitchActivatedAt}
              onToggle={onToggleKillSwitch}
              onDeactivate={onDeactivateKillSwitch}
            />
          </PanelSectionRow>
          <PanelSectionRow>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '8px',
                marginBottom: '4px',
              }}
            >
              <span style={{ fontSize: '14px', fontWeight: 600, color: '#c7d5e0' }}>Reset configuration</span>
              <HelpPopover label="Help: reset configuration" topic="configured.reset" />
            </div>
          </PanelSectionRow>
          <PanelSectionRow>
            <ResetConfigurationButton disabled={isResetDisabled} onReset={onResetConfig} />
          </PanelSectionRow>
        </>
      )}
    </PanelSection>
  )
}
