import { FC, useState } from 'react';
import { DialogButtonPrimary, Field, Toggle } from '@decky/ui';
import { FaPowerOff } from 'react-icons/fa';
import { HelpPopover } from './ui/HelpPopover';
import type { DeactivateKillSwitchResponse, ToggleKillSwitchResponse } from '../services/api';

interface KillSwitchToggleProps {
  enabled: boolean;
  isActive: boolean;
  activatedAt?: number | null;
  onToggle: (enabled: boolean) => Promise<ToggleKillSwitchResponse>;
  onDeactivate: () => Promise<DeactivateKillSwitchResponse>;
}

export const KillSwitchToggle: FC<KillSwitchToggleProps> = ({
  enabled,
  isActive,
  activatedAt,
  onToggle,
  onDeactivate,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const leftDescriptionStyle = { display: 'block', textAlign: 'left' } as const;

  const handleToggle = async (nextEnabled: boolean) => {
    setError(null);
    setLoading(true);

    try {
      const result = await onToggle(nextEnabled);
      if (!result.success) {
        setError('Failed to toggle kill switch');
      }
    } catch (err) {
      console.error('Toggle error:', err);
      setError('Network error. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeactivate = async () => {
    setError(null);
    setLoading(true);

    try {
      const result = await onDeactivate();
      if (!result.success) {
        setError(result.error || 'Failed to deactivate kill switch');
      }
    } catch (err) {
      console.error('Deactivate error:', err);
      setError('Network error. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (timestamp: number | null): string => {
    if (!timestamp) return '';
    return new Date(timestamp * 1000).toLocaleString();
  };

  return (
    <div style={{ padding: '10px' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '8px',
          marginBottom: '4px',
        }}
      >
        <span style={{ fontSize: '14px', fontWeight: 600, color: '#c7d5e0' }}>Kill Switch</span>
        <HelpPopover label="Help: Kill switch" topic="options.kill_switch" />
      </div>

      <div style={{ marginBottom: '15px' }}>
        <Field
          label="Enable Kill Switch"
          description={
            <span style={leftDescriptionStyle}>
              Blocks all traffic if the proxy disconnects unexpectedly.
            </span>
          }
          bottomSeparator="none"
          highlightOnFocus
          childrenLayout="inline"
        >
          <Toggle value={enabled} disabled={loading} onChange={handleToggle} />
        </Field>

        {isActive && (
          <div
            style={{
              marginTop: '12px',
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
              All system traffic is currently blocked. This happened because the proxy disconnected
              unexpectedly.
            </p>
            {activatedAt && (
              <p style={{ marginTop: '5px', fontSize: '12px' }}>
                Activated at: {formatTime(activatedAt)}
              </p>
            )}
            <DialogButtonPrimary
              onClick={handleDeactivate}
              disabled={loading}
              style={{ width: '100%' }}
            >
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                <FaPowerOff />
                {loading ? 'Deactivating...' : 'Deactivate Kill Switch'}
              </span>
            </DialogButtonPrimary>
          </div>
        )}

        {enabled && !isActive && (
          <div
            style={{
              marginTop: '12px',
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
            <p style={{ marginTop: '5px' }}>
              Traffic will be blocked if the proxy disconnects unexpectedly.
            </p>
          </div>
        )}

        {error && (
          <div
            style={{
              marginTop: '12px',
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
    </div>
  );
};
