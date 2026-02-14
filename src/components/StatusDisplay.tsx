import { FC } from 'react';
import { Field } from '@decky/ui';
import type { ConnectionStatus } from '../services/api';

interface StatusDisplayProps {
  status: ConnectionStatus;
  errorMessage?: string | null;
  uptime?: number | null;
  connectedAt?: number | null;
}

export const StatusDisplay: FC<StatusDisplayProps> = ({
  status,
  errorMessage,
  uptime,
  connectedAt,
}) => {
  const leftDescriptionStyle = { display: 'block', textAlign: 'left' } as const;
  const getStatusColor = (): string => {
    switch (status) {
      case 'connected':
        return '#6bff6b';
      case 'connecting':
        return '#ffd93d';
      case 'error':
        return '#ff6b6b';
      case 'blocked':
        return '#ff6b6b';
      default:
        return '#aaa';
    }
  };

  const getStatusText = (): string => {
    switch (status) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'error':
        return 'Error';
      case 'blocked':
        return 'Blocked (Kill Switch)';
      default:
        return 'Disconnected';
    }
  };

  const formatUptime = (seconds?: number | null): string => {
    if (!seconds) return '';

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const cardStyle = {
    padding: '10px',
    backgroundColor: '#1b2a3a',
    borderRadius: '6px',
    marginBottom: '10px',
  };

  const statusIndicator = (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
      <span
        style={{
          width: '10px',
          height: '10px',
          borderRadius: '50%',
          backgroundColor: getStatusColor(),
          display: 'inline-block',
        }}
      />
      <span style={{ fontWeight: 600 }}>{getStatusText()}</span>
    </span>
  );

  return (
    <div style={cardStyle}>
      <Field
        label="Connection status"
        bottomSeparator="none"
        description={<span style={leftDescriptionStyle}>{statusIndicator}</span>}
      />

      {status === 'connected' && uptime != null && (
        <Field
          label="Uptime"
          bottomSeparator="none"
          description={<span style={leftDescriptionStyle}>{formatUptime(uptime)}</span>}
        />
      )}
      {status === 'connected' && connectedAt && (
        <Field
          label="Connected at"
          bottomSeparator="none"
          description={
            <span style={leftDescriptionStyle}>
              {new Date(connectedAt * 1000).toLocaleString()}
            </span>
          }
        />
      )}

      {status === 'error' && errorMessage && (
        <Field
          label="Error"
          bottomSeparator="none"
          description={
            <span style={{ ...leftDescriptionStyle, color: '#ff6b6b' }}>{errorMessage}</span>
          }
        />
      )}

      {status === 'blocked' && (
        <Field
          label="Kill Switch"
          bottomSeparator="none"
          description={
            <span style={{ ...leftDescriptionStyle, color: '#ff6b6b' }}>
              All traffic is blocked. Reconnect to restore.
            </span>
          }
        />
      )}
    </div>
  );
};
