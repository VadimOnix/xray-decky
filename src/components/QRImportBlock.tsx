import { FC, useState, useEffect } from 'react'
import { QRCodeSVG } from 'qrcode.react'
import { getImportServerUrl, ImportServerUrlResponse } from '../services/api'

export const QRImportBlock: FC = () => {
  const [urlInfo, setUrlInfo] = useState<ImportServerUrlResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [debugInfo, setDebugInfo] = useState<string>('init')

  // #region agent log - console logging for CEF debug
  console.log('[QRImportBlock] Component rendering, urlInfo:', urlInfo, 'error:', error)
  // #endregion

  useEffect(() => {
    // #region agent log
    console.log('[QRImportBlock] useEffect started')
    setDebugInfo('useEffect started')
    // #endregion

    let cancelled = false

    const fetchUrl = async () => {
      try {
        // #region agent log
        console.log('[QRImportBlock] Calling getImportServerUrl()...')
        setDebugInfo('calling API...')
        // #endregion

        const res = await getImportServerUrl()

        // #region agent log
        console.log('[QRImportBlock] getImportServerUrl() returned:', res)
        // #endregion

        if (!cancelled) {
          setUrlInfo(res)
          setError(null)
          setDebugInfo('success: ' + JSON.stringify(res))
        }
      } catch (err: unknown) {
        // #region agent log
        console.error('[QRImportBlock] getImportServerUrl() error:', err)
        // #endregion

        if (!cancelled) {
          const errMsg = err instanceof Error ? err.message : String(err)
          setError(errMsg)
          setUrlInfo(null)
          setDebugInfo('error: ' + errMsg)
        }
      }
    }

    fetchUrl()

    return () => {
      cancelled = true
    }
  }, [])

  // Always show debug info for troubleshooting
  const debugBlock = (
    <div style={{ padding: '8px', backgroundColor: '#2a2a4a', borderRadius: '4px', marginBottom: '10px', fontSize: '11px', fontFamily: 'monospace' }}>
      <p style={{ color: '#ffd93d', margin: 0 }}>Debug: {debugInfo}</p>
      {error && <p style={{ color: '#ff6b6b', margin: '4px 0 0 0' }}>Error: {error}</p>}
      {urlInfo && <p style={{ color: '#6bff6b', margin: '4px 0 0 0' }}>Data: {JSON.stringify(urlInfo)}</p>}
    </div>
  )

  if (error) {
    return (
      <div style={{ padding: '10px' }}>
        <h2>Import via QR</h2>
        {debugBlock}
        <p style={{ color: '#ff6b6b' }}>{error}</p>
      </div>
    )
  }

  if (!urlInfo) {
    return (
      <div style={{ padding: '10px' }}>
        <h2>Import via QR</h2>
        {debugBlock}
        <p style={{ color: '#8f98a0' }}>Loading…</p>
      </div>
    )
  }

  const importUrl = urlInfo.baseUrl.replace(/\/$/, '') + urlInfo.path

  // #region agent log
  console.log('[QRImportBlock] Rendering QR for URL:', importUrl)
  // #endregion

  return (
    <div style={{ padding: '10px' }}>
      <h2>Import via QR</h2>
      {debugBlock}
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
