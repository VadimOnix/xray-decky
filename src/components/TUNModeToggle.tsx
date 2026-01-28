import { FC, useState, useEffect } from 'react'
import { ServerAPI } from 'decky-frontend-lib'
import { APIService } from '../services/api'

interface TUNModeToggleProps {
  serverAPI: ServerAPI
}

export const TUNModeToggle: FC<TUNModeToggleProps> = ({ serverAPI }) => {
  const [enabled, setEnabled] = useState(false)
  const [hasPrivileges, setHasPrivileges] = useState(false)
  const [loading, setLoading] = useState(false)
  const [checkingPrivileges, setCheckingPrivileges] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tunInterface, setTunInterface] = useState<string | null>(null)
  const [isActive, setIsActive] = useState(false)

  const api = new APIService(serverAPI)

  // Load initial status
  useEffect(() => {
    loadStatus()
    // Poll status every 3 seconds
    const interval = setInterval(loadStatus, 3000)
    return () => clearInterval(interval)
  }, [])

  const loadStatus = async () => {
    try {
      const result = await api.getTUNModeStatus()
      setEnabled(result.enabled)
      setHasPrivileges(result.hasPrivileges)
      setTunInterface(result.tunInterface || null)
      setIsActive(result.isActive)
    } catch (err) {
      console.error('Failed to load TUN mode status:', err)
    }
  }

  const checkPrivileges = async () => {
    setCheckingPrivileges(true)
    setError(null)

    try {
      const result = await api.checkTUNPrivileges()
      setHasPrivileges(result.hasPrivileges)

      if (!result.hasPrivileges && result.error) {
        setError(result.error)
      } else {
        setError(null)
      }
    } catch (err) {
      console.error('Failed to check privileges:', err)
      setError('Failed to check privileges. Please try again.')
    } finally {
      setCheckingPrivileges(false)
    }
  }

  const handleToggle = async () => {
    setError(null)
    setLoading(true)

    try {
      const newState = !enabled
      const result = await api.toggleTUNMode(newState)

      if (result.success) {
        setEnabled(result.enabled)
        setHasPrivileges(result.hasPrivileges)
        setError(null)
      } else {
        const errorMsg = result.error || 'Failed to toggle TUN mode'
        setError(errorMsg)
      }
    } catch (err) {
      console.error('Toggle error:', err)
      setError('Network error. Please check your connection and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '10px', marginTop: '15px' }}>
      <h3>TUN Mode (System-Wide Routing)</h3>

      <div style={{ marginBottom: '15px' }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
          <input
            type="checkbox"
            id="tun-mode-toggle"
            checked={enabled}
            onChange={handleToggle}
            disabled={loading || !hasPrivileges || checkingPrivileges}
            style={{
              width: '20px',
              height: '20px',
              marginRight: '10px',
              cursor: loading || !hasPrivileges || checkingPrivileges ? 'not-allowed' : 'pointer',
            }}
          />
          <label
            htmlFor="tun-mode-toggle"
            style={{
              fontSize: '16px',
              cursor: loading || !hasPrivileges || checkingPrivileges ? 'not-allowed' : 'pointer',
            }}
          >
            Enable TUN Mode
          </label>
        </div>

        {!hasPrivileges && (
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
            <p>
              <strong>Privileges Required:</strong> TUN mode requires elevated privileges.
            </p>
            <p style={{ marginTop: '5px' }}>
              Please complete the installation steps to enable TUN mode. See INSTALLATION.md for details.
            </p>
            <button
              onClick={checkPrivileges}
              disabled={checkingPrivileges}
              style={{
                marginTop: '10px',
                padding: '8px 16px',
                backgroundColor: checkingPrivileges ? '#3a5f8f' : '#5f8f3a',
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                cursor: checkingPrivileges ? 'not-allowed' : 'pointer',
              }}
            >
              {checkingPrivileges ? 'Checking...' : 'Check Privileges'}
            </button>
          </div>
        )}

        {hasPrivileges && enabled && (
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
              <strong>✓ TUN Mode Enabled</strong>
            </p>
            {isActive && tunInterface && <p style={{ marginTop: '5px' }}>Active on interface: {tunInterface}</p>}
            {!isActive && <p style={{ marginTop: '5px' }}>Connect to proxy to activate TUN mode.</p>}
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
            {enabled ? 'Disabling TUN mode...' : 'Enabling TUN mode...'}
          </div>
        )}
      </div>

      <div style={{ fontSize: '12px', color: '#aaa', marginTop: '10px' }}>
        <p>
          <strong>About TUN Mode:</strong>
        </p>
        <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
          <li>Routes all system traffic through the proxy</li>
          <li>Requires elevated privileges (sudo exemption)</li>
          <li>Works system-wide, not just browser/app-specific</li>
          <li>See INSTALLATION.md for setup instructions</li>
        </ul>
      </div>
    </div>
  )
}
