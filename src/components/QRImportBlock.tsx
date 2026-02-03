import { FC, useState, useEffect } from 'react'
import { QRCodeSVG } from 'qrcode.react'
import { getImportServerUrl, ImportServerUrlResponse } from '../services/api'

export const QRImportBlock: FC = () => {
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
      <div style={{ padding: '10px' }}>
        <h2>Import via QR</h2>
        <p style={{ color: '#ff6b6b' }}>{error}</p>
      </div>
    )
  }

  if (!urlInfo) {
    return (
      <div style={{ padding: '10px' }}>
        <h2>Import via QR</h2>
        <p style={{ color: '#8f98a0' }}>Loading…</p>
      </div>
    )
  }

  const importUrl = urlInfo.baseUrl.replace(/\/$/, '') + urlInfo.path

  return (
    <div style={{ padding: '10px' }}>
      <h2>Import via QR</h2>
      <p style={{ color: '#8f98a0', marginBottom: '12px' }}>
        Scan with your phone or open the link below to import your VLESS configuration.
      </p>

      {/* Always show the link as fallback */}
      <div style={{ marginBottom: '12px', padding: '10px', backgroundColor: '#1e3a5f', borderRadius: '5px' }}>
        <p style={{ fontSize: '14px', color: '#c7d5e0', marginBottom: '8px' }}>
          <strong>Import URL:</strong>
        </p>
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

      {/* QR code section */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
        <QRCodeSVG value={importUrl} size={180} level="M" />
      </div>
    </div>
  )
}
