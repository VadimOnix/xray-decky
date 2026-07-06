import { FC, useEffect, useState } from 'react';
import { Field } from '@decky/ui';
import { getTrafficStats, type ConnectionStatus } from '../services/api';
import { t } from '../utils/i18n';

interface StatusDisplayProps {
  status: ConnectionStatus;
  errorMessage?: string | null;
  uptime?: number | null;
  connectedAt?: number | null;
}

const STATS_POLL_MS = 2000;

const formatBytes = (bytes: number, perSecond: boolean): string => {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let value = Math.max(0, bytes || 0);
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value = value / 1024;
    unit++;
  }
  const text = `${unit === 0 ? value : value.toFixed(1)} ${units[unit]}`;
  return perSecond ? `${text}/s` : text;
};

interface Speeds {
  down: number;
  up: number;
  total: number;
}

export const StatusDisplay: FC<StatusDisplayProps> = ({
  status,
  errorMessage,
  uptime,
  connectedAt,
}) => {
  const leftDescriptionStyle = { display: 'block', textAlign: 'left' } as const;
  const [speeds, setSpeeds] = useState<Speeds | null>(null);

  useEffect(() => {
    if (status !== 'connected') {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- clear stale speeds when leaving the connected state
      setSpeeds(null);
      return;
    }
    let cancelled = false;
    const poll = async () => {
      try {
        const result = await getTrafficStats();
        if (cancelled) return;
        if (result.success && result.available) {
          setSpeeds({
            down: result.downlinkSpeed,
            up: result.uplinkSpeed,
            total: result.uplink + result.downlink,
          });
        }
      } catch {
        /* transient */
      }
    };
    void poll();
    const interval = setInterval(() => void poll(), STATS_POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [status]);

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
        return t('status.connected');
      case 'connecting':
        return t('status.connecting');
      case 'error':
        return t('status.error');
      case 'blocked':
        return t('status.blocked');
      default:
        return t('status.disconnected');
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
        label={t('status.title')}
        bottomSeparator="none"
        description={<span style={leftDescriptionStyle}>{statusIndicator}</span>}
      />

      {status === 'connected' && uptime != null && (
        <Field
          label={t('status.uptime')}
          bottomSeparator="none"
          description={<span style={leftDescriptionStyle}>{formatUptime(uptime)}</span>}
        />
      )}
      {status === 'connected' && connectedAt && (
        <Field
          label={t('status.connectedAt')}
          bottomSeparator="none"
          description={
            <span style={leftDescriptionStyle}>
              {new Date(connectedAt * 1000).toLocaleString()}
            </span>
          }
        />
      )}
      {status === 'connected' && speeds && (
        <Field
          label={t('status.speed')}
          bottomSeparator="none"
          description={
            <span style={{ ...leftDescriptionStyle, fontVariant: 'tabular-nums' }}>
              <span style={{ color: '#a1cd44' }}>▼ {formatBytes(speeds.down, true)}</span>
              {'   '}
              <span style={{ color: '#66c0f4' }}>▲ {formatBytes(speeds.up, true)}</span>
              {'   '}
              <span style={{ color: '#8f98a0' }}>
                {formatBytes(speeds.total, false)} {t('status.total')}
              </span>
            </span>
          }
        />
      )}

      {status === 'error' && errorMessage && (
        <Field
          label={t('status.errorLabel')}
          bottomSeparator="none"
          description={
            <span style={{ ...leftDescriptionStyle, color: '#ff6b6b' }}>{errorMessage}</span>
          }
        />
      )}

      {status === 'blocked' && (
        <Field
          label={t('status.killSwitch')}
          bottomSeparator="none"
          description={
            <span style={{ ...leftDescriptionStyle, color: '#ff6b6b' }}>
              {t('status.blockedMsg')}
            </span>
          }
        />
      )}
    </div>
  );
};
