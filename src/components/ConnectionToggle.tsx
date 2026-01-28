import { FC, useState, useEffect } from 'react'
import { ServerAPI } from 'decky-frontend-lib'
import { APIService, ConnectionStatus } from '../services/api'

interface ConnectionToggleProps {
  serverAPI: ServerAPI
}

export const ConnectionToggle: FC<ConnectionToggleProps> = ({ serverAPI }) => {
  const [isEnabled, setIsEnabled] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState<ConnectionStatus>('disconnected')

  const api = new APIService(serverAPI)

  // Load initial status
  useEffect(() => {
    loadStatus()
    // Poll status every 2 seconds
    const interval = setInterval(loadStatus, 2000)
    return () => clearInterval(interval)
  }, [])

  const loadStatus = async () => {
    try {
      const result = await api.getConnectionStatus()
      setStatus(result.status)
      setIsEnabled(result.status === 'connected' || result.status === 'connecting')
    } catch (err) {
      console.error('Failed to load connection status:', err)
    }
  }

  const handleToggle = async () => {
    setError(null)
    setLoading(true)

    try {
      const newState = !isEnabled
      const result = await api.toggleConnection(newState)

      if (result.success) {
        setIsEnabled(newState)
        setStatus(result.status)
        setError(null)
      } else {
        const errorMsg = result.error || 'Failed to toggle connection'
        setError(errorMsg)
        setIsEnabled(false)
        setStatus('error')
      }
    } catch (err) {
      console.error('Toggle error:', err)
      setError('Network error. Please check your connection and try again.')
      setIsEnabled(false)
      setStatus('error')
    } finally {
      setLoading(false)
    }
  }

  const getToggleLabel = (): string => {
    if (loading) {
      return status === 'connecting' ? 'Connecting...' : 'Disconnecting...'
    }
    return isEnabled ? 'Disconnect' : 'Connect'
  }

  const isToggleDisabled = (): boolean => {
    return loading || status === 'connecting' || status === 'blocked'
  }

  return (
    <div style={{ padding: '10px' }}>
      <h3>Connection Control</h3>

      <div style={{ marginBottom: '15px' }}>
        <button
          onClick={handleToggle}
          disabled={isToggleDisabled()}
          style={{
            padding: '15px 30px',
            fontSize: '18px',
            fontWeight: 'bold',
            backgroundColor: isEnabled ? (loading ? '#3a5f8f' : '#ff6b6b') : loading ? '#3a5f8f' : '#5f8f3a',
            color: '#fff',
            border: 'none',
            borderRadius: '5px',
            cursor: isToggleDisabled() ? 'not-allowed' : 'pointer',
            width: '100%',
            transition: 'background-color 0.2s',
          }}
        >
          {getToggleLabel()}
        </button>
      </div>

      {error && (
        <div
          style={{
            marginTop: '10px',
            padding: '10px',
            backgroundColor: '#5f1e1e',
            color: '#ff6b6b',
            borderRadius: '5px',
            fontSize: '14px',
          }}
        >
          <strong>Error:</strong> {error}
        </div>
      )}

      {status === 'blocked' && (
        <div
          style={{
            marginTop: '10px',
            padding: '10px',
            backgroundColor: '#5f1e1e',
            color: '#ff6b6b',
            borderRadius: '5px',
            fontSize: '14px',
          }}
        >
          <strong>Kill Switch Active:</strong> Connection is blocked. Please disable kill switch first.
        </div>
      )}

      {!error && status !== 'blocked' && (
        <div style={{ marginTop: '10px', fontSize: '12px', color: '#aaa' }}>
          {isEnabled ? (
            <p>Proxy is active. Click to disconnect.</p>
          ) : (
            <p>Proxy is inactive. Make sure you have imported a VLESS configuration first.</p>
          )}
        </div>
      )}
    </div>
  )
}
