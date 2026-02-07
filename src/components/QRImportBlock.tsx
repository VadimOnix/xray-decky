import { FC, useEffect, useState } from 'react'
import { Focusable } from '@decky/ui'
import { QRCodeSVG } from 'qrcode.react'
import { getImportServerUrl, ImportServerUrlResponse } from '../services/api'
import { HelpPopover } from './ui/HelpPopover'
import type { HelpTopic } from '../types/ui'

interface QRImportBlockProps {
  helpTopicQr?: HelpTopic
  helpTopicLan?: HelpTopic
}

const headerRowStyle = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: '8px',
}

const headerLabelStyle = {
  fontSize: '14px',
  fontWeight: 600,
  color: '#c7d5e0',
}

export const QRImportBlock: FC<QRImportBlockProps> = ({ helpTopicQr, helpTopicLan }) => {
  const [urlInfo, setUrlInfo] = useState<ImportServerUrlResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    const fetchUrl = async () => {
      try {
        const res = await getImportServerUrl()
        if (!cancelled) {
          setUrlInfo(res)
          setError(null)
        }
      } catch (err: unknown) {
        if (!cancelled) {
          const errMsg = err instanceof Error ? err.message : String(err)
          setError(errMsg)
          setUrlInfo(null)
        }
      }
    }

    fetchUrl()

    return () => {
      cancelled = true
    }
  }, [])

  if (error) {
    return (
      <div>
        <div style={headerRowStyle}>
          <span style={headerLabelStyle}>Import via QR</span>
          {helpTopicQr && <HelpPopover label="Help: QR import" topic={helpTopicQr} />}
        </div>
        <p style={{ color: '#ff6b6b', marginTop: '8px' }}>{error}</p>
      </div>
    )
  }

  if (!urlInfo) {
    return (
      <div>
        <div style={headerRowStyle}>
          <span style={headerLabelStyle}>Import via QR</span>
          {helpTopicQr && <HelpPopover label="Help: QR import" topic={helpTopicQr} />}
        </div>
        <p style={{ color: '#8f98a0', marginTop: '8px' }}>Loading import address…</p>
      </div>
    )
  }

  const importUrl = urlInfo.baseUrl.replace(/\/$/, '') + urlInfo.path

  return (
    <div>
      <div style={headerRowStyle}>
        <span style={headerLabelStyle}>Import via QR</span>
        {helpTopicQr && <HelpPopover label="Help: QR import" topic={helpTopicQr} />}
      </div>
      <p style={{ color: '#8f98a0', marginBottom: '12px' }}>
        Scan with your phone or open the link below to import your VLESS configuration.
      </p>

      {/* QR code section */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
        <QRCodeSVG value={importUrl} size={180} level="M" />
      </div>

      <Focusable>
        <div style={{ marginBottom: '12px', padding: '10px', backgroundColor: '#1e3a5f', borderRadius: '5px' }}>
          <div style={headerRowStyle}>
            <span style={{ fontSize: '14px', color: '#c7d5e0' }}>Import URL</span>
            {helpTopicLan && <HelpPopover label="Help: LAN address" topic={helpTopicLan} />}
          </div>
          <p
            style={{
              fontSize: '14px',
              color: '#66c0f4',
              wordBreak: 'break-all',
              fontFamily: 'monospace',
            }}
          >
            {importUrl}
          </p>
        </div>
      </Focusable>
    </div>
  )
}
