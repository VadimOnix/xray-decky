import { FC, useState } from 'react';
import { DialogButtonPrimary, Field, Toggle } from '@decky/ui';
import { FaPowerOff } from 'react-icons/fa';
import { HelpPopover } from './ui/HelpPopover';
import type { DeactivateKillSwitchResponse, ToggleKillSwitchResponse } from '../services/api';
import { t } from '../utils/i18n';

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
        setError(t('ks.toggleFail'));
      }
    } catch (err) {
      console.error('Toggle error:', err);
      setError(t('common.netErr'));
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
        setError(result.error || t('ks.deactivateFail'));
      }
    } catch (err) {
      console.error('Deactivate error:', err);
      setError(t('common.netErr'));
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
        <span style={{ fontSize: '14px', fontWeight: 600, color: '#c7d5e0' }}>{t('ks.title')}</span>
        <HelpPopover label={t('ks.help')} topic="options.kill_switch" />
      </div>

      <div style={{ marginBottom: '15px' }}>
        <Field
          label={t('ks.enable')}
          description={<span style={leftDescriptionStyle}>{t('ks.enableDesc')}</span>}
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
              <strong>{t('ks.activeTitle')}</strong>
            </p>
            <p style={{ marginTop: '5px' }}>{t('ks.activeMsg')}</p>
            {activatedAt && (
              <p style={{ marginTop: '5px', fontSize: '12px' }}>
                {t('ks.activatedAt', { time: formatTime(activatedAt) })}
              </p>
            )}
            <DialogButtonPrimary
              onClick={handleDeactivate}
              disabled={loading}
              style={{ width: '100%' }}
            >
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                <FaPowerOff />
                {loading ? t('ks.deactivating') : t('ks.deactivate')}
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
              <strong>{t('ks.enabledTitle')}</strong>
            </p>
            <p style={{ marginTop: '5px' }}>{t('ks.enabledMsg')}</p>
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
            <strong>{t('common.errorLabel')}</strong> {error}
          </div>
        )}

        {loading && (
          <div style={{ marginTop: '10px', color: '#aaa', fontSize: '14px' }}>
            {enabled ? t('ks.disabling') : t('ks.enabling')}
          </div>
        )}
      </div>
    </div>
  );
};
