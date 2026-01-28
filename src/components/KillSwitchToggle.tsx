import { FC, useState, useEffect } from 'react'
import { ServerAPI } from 'decky-frontend-lib'
import { APIService } from '../services/api'

interface KillSwitchToggleProps {
  serverAPI: ServerAPI
}

export const KillSwitchToggle: FC<KillSwitchToggleProps> = ({ serverAPI }) => {
  const [enabled, setEnabled] = useState(false)
  const [isActive, setIsActive] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activatedAt, setActivatedAt] = useState<number | null>(null)

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
      const result = await api.getKillSwitchStatus()
      setEnabled(result.enabled)
      setIsActive(result.isActive)
      setActivatedAt(result.activatedAt || null)
    } catch (err) {
      console.error('Failed to load kill switch status:', err)
    }
  }

  const handleToggle = async () => {
    setError(null)
    setLoading(true)

    try {
      const newState = !enabled
      const result = await api.toggleKillSwitch(newState)

      if (result.success) {
        setEnabled(result.enabled)
        setError(null)
      } else {
        const errorMsg = 'Failed to toggle kill switch'
        setError(errorMsg)
      }
    } catch (err) {
      console.error('Toggle error:', err)
      setError('Network error. Please check your connection and try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleDeactivate = async () => {
    setError(null)
    setLoading(true)

    try {
      const result = await api.deactivateKillSwitch()

      if (result.success) {
        setIsActive(false)
        setActivatedAt(null)
        setError(null)
      } else {
        const errorMsg = result.error || 'Failed to deactivate kill switch'
        setError(errorMsg)
      }
    } catch (err) {
      console.error('Deactivate error:', err)
      setError('Network error. Please check your connection and try again.')
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (timestamp: number | null): string => {
    if (!timestamp) return ''
    return new Date(timestamp * 1000).toLocaleString()
  }

  return (
    <div style={{ padding: '10px', marginTop: '15px' }}>
      <h3>Kill Switch</h3>

      <div style={{ marginBottom: '15px' }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
          <input
            type="checkbox"
            id="kill-switch-toggle"
            checked={enabled}
            onChange={handleToggle}
            disabled={loading}
            style={{
              width: '20px',
              height: '20px',
              marginRight: '10px',
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          />
          <label
            htmlFor="kill-switch-toggle"
            style={{
              fontSize: '16px',
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            Enable Kill Switch
          </label>
        </div>

        {isActive && (
          <div
            style={{
              padding: '15px',
              backgroundColor: '#5f1e1e',
              color: '#ff6b6b',
              borderRadius: '5px',
              marginBottom: '10px',
              fontSize: '14px',
            }}
          >
            <p>
              <strong>⚠️ KILL SWITCH ACTIVE</strong>
            </p>
            <p style={{ marginTop: '5px' }}>
              All system traffic is currently blocked. This happened because the proxy disconnected unexpectedly.
            </p>
            {activatedAt && (
              <p style={{ marginTop: '5px', fontSize: '12px' }}>Activated at: {formatTime(activatedAt)}</p>
            )}
            <button
              onClick={handleDeactivate}
              disabled={loading}
              style={{
                marginTop: '10px',
                padding: '10px 20px',
                fontSize: '16px',
                backgroundColor: loading ? '#3a5f8f' : '#ff6b6b',
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                cursor: loading ? 'not-allowed' : 'pointer',
                fontWeight: 'bold',
              }}
            >
              {loading ? 'Deactivating...' : 'Deactivate Kill Switch'}
            </button>
          </div>
        )}

        {enabled && !isActive && (
          <div
            style={{
              padding: '10px',
              backgroundColor: '#1e5f1e',
              color: '#6bff6b',
              borderRadius: '5px',
              marginBottom: '10px',
              fontSize: '14px',
            }}
          >
            <p>
              <strong>✓ Kill Switch Enabled</strong>
            </p>
            <p style={{ marginTop: '5px' }}>Traffic will be blocked if the proxy disconnects unexpectedly.</p>
          </div>
        )}

        {error && (
          <div
            style={{
              padding: '10px',
              backgroundColor: '#5f1e1e',
              color: '#ff6b6b',
              borderRadius: '5px',
              marginBottom: '10px',
              fontSize: '14px',
            }}
          >
            <strong>Error:</strong> {error}
          </div>
        )}

        {loading && (
          <div style={{ marginTop: '10px', color: '#aaa', fontSize: '14px' }}>
            {enabled ? 'Disabling kill switch...' : 'Enabling kill switch...'}
          </div>
        )}
      </div>

      <div style={{ fontSize: '12px', color: '#aaa', marginTop: '10px' }}>
        <p>
          <strong>About Kill Switch:</strong>
        </p>
        <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
          <li>Blocks all system traffic when proxy disconnects unexpectedly</li>
          <li>Prevents clearnet leaks if connection fails</li>
          <li>Off by default - enable only if needed</li>
          <li>Requires iptables (standard on Linux)</li>
        </ul>
      </div>
    </div>
  )
}
