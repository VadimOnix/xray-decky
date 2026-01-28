import { FC, useState, useEffect } from 'react'
import { ServerAPI } from 'decky-frontend-lib'
import { APIService, VLESSConfig } from '../services/api'
import { validateVLESSURL, getValidationErrorMessage } from '../utils/validation'

interface ConfigImportProps {
  serverAPI: ServerAPI
}

export const ConfigImport: FC<ConfigImportProps> = ({ serverAPI }) => {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [storedConfig, setStoredConfig] = useState<VLESSConfig | null>(null)

  const api = new APIService(serverAPI)

  // Load existing config on mount
  useEffect(() => {
    loadStoredConfig()
  }, [])

  const loadStoredConfig = async () => {
    try {
      const result = await api.getVLESSConfig()
      if (result.exists && result.config) {
        setStoredConfig(result.config)
        setUrl(result.config.sourceUrl)
      }
    } catch (err) {
      console.error('Failed to load stored config:', err)
    }
  }

  const handleImport = async () => {
    // Clear previous errors/success
    setError(null)
    setSuccess(false)
    setLoading(true)

    try {
      // Frontend validation
      if (!url.trim()) {
        setError('Please enter a VLESS URL')
        setLoading(false)
        return
      }

      if (!validateVLESSURL(url.trim())) {
        setError('Invalid VLESS URL format. Please check the URL and try again.')
        setLoading(false)
        return
      }

      // Call backend API
      const result = await api.importVLESSConfig(url.trim())

      if (result.success && result.config) {
        setStoredConfig(result.config)
        setSuccess(true)
        setError(null)
        // Clear success message after 3 seconds
        setTimeout(() => setSuccess(false), 3000)
      } else {
        const errorMsg = result.error || 'Failed to import configuration'
        setError(getValidationErrorMessage(errorMsg))
      }
    } catch (err) {
      console.error('Import error:', err)
      setError('Network error. Please check your connection and try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleReplace = () => {
    setStoredConfig(null)
    setUrl('')
    setError(null)
    setSuccess(false)
  }

  return (
    <div style={{ padding: '10px' }}>
      <h2>Import VLESS Configuration</h2>

      {storedConfig && (
        <div
          style={{
            marginBottom: '15px',
            padding: '10px',
            backgroundColor: '#1e3a5f',
            borderRadius: '5px',
          }}
        >
          <p>
            <strong>Current Configuration:</strong>
          </p>
          <p>Type: {storedConfig.configType}</p>
          <p>
            Address: {storedConfig.address}:{storedConfig.port}
          </p>
          {storedConfig.name && <p>Name: {storedConfig.name}</p>}
          <p>Status: {storedConfig.isValid ? '✓ Valid' : '✗ Invalid'}</p>
          <button onClick={handleReplace} style={{ marginTop: '10px', padding: '5px 10px' }}>
            Replace Configuration
          </button>
        </div>
      )}

      <div style={{ marginBottom: '10px' }}>
        <label htmlFor="vless-url" style={{ display: 'block', marginBottom: '5px' }}>
          VLESS URL:
        </label>
        <input
          id="vless-url"
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="vless://uuid@host:port?params#name"
          disabled={loading}
          style={{
            width: '100%',
            padding: '8px',
            fontSize: '14px',
            backgroundColor: '#1e3a5f',
            color: '#fff',
            border: '1px solid #3a5f8f',
            borderRadius: '4px',
          }}
          onKeyPress={(e) => {
            if (e.key === 'Enter' && !loading) {
              handleImport()
            }
          }}
        />
      </div>

      {error && (
        <div
          style={{
            marginBottom: '10px',
            padding: '10px',
            backgroundColor: '#5f1e1e',
            color: '#ff6b6b',
            borderRadius: '5px',
          }}
        >
          <strong>Error:</strong> {error}
        </div>
      )}

      {success && (
        <div
          style={{
            marginBottom: '10px',
            padding: '10px',
            backgroundColor: '#1e5f1e',
            color: '#6bff6b',
            borderRadius: '5px',
          }}
        >
          <strong>Success:</strong> Configuration imported successfully!
        </div>
      )}

      <button
        onClick={handleImport}
        disabled={loading || !url.trim()}
        style={{
          padding: '10px 20px',
          fontSize: '16px',
          backgroundColor: loading ? '#3a5f8f' : '#5f8f3a',
          color: '#fff',
          border: 'none',
          borderRadius: '4px',
          cursor: loading ? 'not-allowed' : 'pointer',
        }}
      >
        {loading ? 'Importing...' : storedConfig ? 'Update Configuration' : 'Import Configuration'}
      </button>

      <div style={{ marginTop: '15px', fontSize: '12px', color: '#aaa' }}>
        <p>Supported formats:</p>
        <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
          <li>Single node: vless://uuid@host:port?params#name</li>
          <li>Subscription: Base64-encoded JSON array</li>
        </ul>
      </div>
    </div>
  )
}
