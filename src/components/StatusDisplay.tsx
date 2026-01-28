import { FC, useEffect, useState } from 'react'
import { ServerAPI } from 'decky-frontend-lib'
import { APIService, ConnectionStatus } from '../services/api'

interface StatusDisplayProps {
  serverAPI: ServerAPI
}

export const StatusDisplay: FC<StatusDisplayProps> = ({ serverAPI }) => {
  const [status, setStatus] = useState<ConnectionStatus>('disconnected')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [uptime, setUptime] = useState<number | null>(null)
  const [processId, setProcessId] = useState<number | null>(null)
  const [connectedAt, setConnectedAt] = useState<number | null>(null)

  const api = new APIService(serverAPI)

  useEffect(() => {
    // Poll connection status
    const pollStatus = async () => {
      try {
        const result = await api.getConnectionStatus()
        setStatus(result.status)
        setErrorMessage(result.errorMessage || null)
        setUptime(result.uptime || null)
        setProcessId(result.processId || null)
        setConnectedAt(result.connectedAt || null)
      } catch (err) {
        console.error('Failed to get connection status:', err)
      }
    }

    // Initial poll
    pollStatus()

    // Poll every 2 seconds
    const interval = setInterval(pollStatus, 2000)

    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (): string => {
    switch (status) {
      case 'connected':
        return '#6bff6b'
      case 'connecting':
        return '#ffd93d'
      case 'error':
        return '#ff6b6b'
      case 'blocked':
        return '#ff6b6b'
      default:
        return '#aaa'
    }
  }

  const getStatusText = (): string => {
    switch (status) {
      case 'connected':
        return 'Connected'
      case 'connecting':
        return 'Connecting...'
      case 'error':
        return 'Error'
      case 'blocked':
        return 'Blocked (Kill Switch)'
      default:
        return 'Disconnected'
    }
  }

  const formatUptime = (seconds: number | null): string => {
    if (!seconds) return ''

    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`
    } else {
      return `${secs}s`
    }
  }

  return (
    <div
      style={{
        padding: '10px',
        marginBottom: '15px',
        backgroundColor: '#1e3a5f',
        borderRadius: '5px',
      }}
    >
      <h3>Connection Status</h3>

      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '10px' }}>
        <div
          style={{
            width: '12px',
            height: '12px',
            borderRadius: '50%',
            backgroundColor: getStatusColor(),
            marginRight: '10px',
            display: 'inline-block',
          }}
        />
        <span style={{ fontSize: '18px', fontWeight: 'bold' }}>{getStatusText()}</span>
      </div>

      {status === 'connected' && (
        <div style={{ marginTop: '10px', fontSize: '14px', color: '#aaa' }}>
          {uptime !== null && <p>Uptime: {formatUptime(uptime)}</p>}
          {processId && <p>Process ID: {processId}</p>}
          {connectedAt && <p>Connected at: {new Date(connectedAt * 1000).toLocaleString()}</p>}
        </div>
      )}

      {status === 'error' && errorMessage && (
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
          <strong>Error:</strong> {errorMessage}
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
          <strong>Kill Switch Active:</strong> All traffic is blocked. Reconnect to restore.
        </div>
      )}
    </div>
  )
}
