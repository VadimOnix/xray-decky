import type { CSSProperties, ReactNode } from 'react'
import { quickAccessMenuClasses } from '@decky/ui'

interface PanelSectionProps {
  title?: string
  children: ReactNode
}

export function PanelSection({ title, children }: PanelSectionProps) {
  return (
    <div className={quickAccessMenuClasses.PanelSection}>
      {title && <div className={quickAccessMenuClasses.PanelSectionTitle}>{title}</div>}
      {children}
    </div>
  )
}

export function PanelSectionRow({ children }: { children: ReactNode }) {
  return <div className={quickAccessMenuClasses.PanelSectionRow}>{children}</div>
}

const helpButtonStyle: CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  width: '18px',
  height: '18px',
  borderRadius: '999px',
  border: '1px solid #3a5f8f',
  background: 'transparent',
  color: '#c7d5e0',
  fontSize: '12px',
  lineHeight: 1,
  marginLeft: '6px',
  cursor: 'pointer',
}

export function HelpIconButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button type="button" aria-label={label} onClick={onClick} style={helpButtonStyle}>
      ?
    </button>
  )
}
