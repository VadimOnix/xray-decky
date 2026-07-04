import { FC, useMemo, useState } from 'react';
import { Field, Toggle } from '@decky/ui';
import type { ConnectionStatus, ToggleConnectionResponse } from '../services/api';
import { t } from '../utils/i18n';

interface ConnectionToggleProps {
  status: ConnectionStatus;
  onToggle: (enable: boolean) => Promise<ToggleConnectionResponse>;
}

export const ConnectionToggle: FC<ConnectionToggleProps> = ({ status, onToggle }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const leftDescriptionStyle = { display: 'block', textAlign: 'left' } as const;

  const isEnabled = status === 'connected' || status === 'connecting';

  const isToggleDisabled = useMemo(() => {
    return loading || status === 'connecting' || status === 'blocked';
  }, [loading, status]);

  const description = useMemo(() => {
    if (status === 'blocked') {
      return t('conn.blockedDesc');
    }
    if (loading) {
      return status === 'connecting' ? t('conn.connecting') : t('conn.disconnecting');
    }
    return isEnabled ? t('conn.active') : t('conn.inactive');
  }, [isEnabled, loading, status]);

  const handleToggle = async (nextEnabled: boolean) => {
    setError(null);
    setLoading(true);

    try {
      const result = await onToggle(nextEnabled);
      if (!result.success) {
        setError(result.error || t('conn.toggleFail'));
      }
    } catch (err) {
      console.error('Toggle error:', err);
      setError(t('conn.netErr'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '10px' }}>
      <Field
        label={t('conn.enable')}
        description={<span style={leftDescriptionStyle}>{description}</span>}
        highlightOnFocus
        childrenLayout="inline"
        bottomSeparator="none"
      >
        <Toggle value={isEnabled} disabled={isToggleDisabled} onChange={handleToggle} />
      </Field>

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
          <strong>{t('conn.errorLabel')}</strong> {error}
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
          <strong>{t('conn.ksActiveLabel')}</strong> {t('conn.ksActiveMsg')}
        </div>
      )}
    </div>
  );
};
