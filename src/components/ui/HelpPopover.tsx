import { FC, useEffect, useMemo, useRef, useState } from 'react'
import type { CSSProperties } from 'react'
import { getHelpContent } from '../../utils/helpContent'
import type { HelpTopic } from '../../types/ui'
import { HelpIconButton } from './primitives'

interface HelpPopoverProps {
  topic: HelpTopic
  label: string
}

export const HelpPopover: FC<HelpPopoverProps> = ({ topic, label }) => {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLSpanElement | null>(null)
  const content = useMemo(() => getHelpContent(topic), [topic])

  const containerStyle: CSSProperties = {
    position: 'relative',
    display: 'inline-flex',
    alignItems: 'center',
  }

  const popoverStyle: CSSProperties = {
    position: 'absolute',
    top: '22px',
    right: 0,
    backgroundColor: '#1b2a3a',
    border: '1px solid #3a5f8f',
    borderRadius: '6px',
    padding: '10px',
    minWidth: '220px',
    maxWidth: '320px',
    zIndex: 20,
    boxShadow: '0 8px 24px rgba(0, 0, 0, 0.35)',
  }

  const headerStyle: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '8px',
    marginBottom: '6px',
    color: '#c7d5e0',
    fontSize: '13px',
    fontWeight: 600,
  }

  const bodyStyle: CSSProperties = {
    color: '#c7d5e0',
    fontSize: '12px',
    lineHeight: 1.35,
    whiteSpace: 'normal',
  }

  const closeButtonStyle: CSSProperties = {
    border: 'none',
    background: 'transparent',
    color: '#c7d5e0',
    cursor: 'pointer',
    fontSize: '12px',
    lineHeight: 1,
    padding: 0,
  }

  const handleToggle = () => {
    setIsOpen((prev) => !prev)
  }

  useEffect(() => {
    if (!isOpen) return

    const handlePointerDown = (event: MouseEvent | TouchEvent) => {
      if (!containerRef.current) return
      if (event.target instanceof Node && containerRef.current.contains(event.target)) {
        return
      }
      setIsOpen(false)
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handlePointerDown)
    document.addEventListener('touchstart', handlePointerDown)
    document.addEventListener('keydown', handleKeyDown)

    return () => {
      document.removeEventListener('mousedown', handlePointerDown)
      document.removeEventListener('touchstart', handlePointerDown)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen])

  return (
    <span ref={containerRef} style={containerStyle}>
      <HelpIconButton label={label} onClick={handleToggle} />
      {isOpen && (
        <div style={popoverStyle} role="dialog" aria-label={content.title}>
          <div style={headerStyle}>
            <span>{content.title}</span>
            <button type="button" aria-label="Close help" style={closeButtonStyle} onClick={handleToggle}>
              x
            </button>
          </div>
          <div style={bodyStyle}>{content.body}</div>
        </div>
      )}
    </span>
  )
}
