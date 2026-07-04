import { FC, useState } from 'react';
import { DialogButton, Field, Toggle } from '@decky/ui';
import { FaShieldAlt } from 'react-icons/fa';
import { HelpPopover } from './ui/HelpPopover';
import type { CheckPrivilegesResponse, ToggleTUNModeResponse } from '../services/api';
import { t } from '../utils/i18n';

interface TUNModeToggleProps {
  enabled: boolean;
  hasPrivileges: boolean;
  isActive: boolean;
  tunInterface?: string | null;
  onToggle: (enabled: boolean) => Promise<ToggleTUNModeResponse>;
  onCheckPrivileges: () => Promise<CheckPrivilegesResponse>;
}

export const TUNModeToggle: FC<TUNModeToggleProps> = ({
  enabled,
  hasPrivileges,
  isActive,
  tunInterface,
  onToggle,
  onCheckPrivileges,
}) => {
  const [loading, setLoading] = useState(false);
  const [checkingPrivileges, setCheckingPrivileges] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const leftDescriptionStyle = { display: 'block', textAlign: 'left' } as const;

  const handleCheckPrivileges = async () => {
    setCheckingPrivileges(true);
    setError(null);

    try {
      const result = await onCheckPrivileges();
      if (!result.hasPrivileges && result.error) {
        setError(result.error);
      }
    } catch (err) {
      console.error('Failed to check privileges:', err);
      setError(t('tun.checkFail'));
    } finally {
      setCheckingPrivileges(false);
    }
  };

  const handleToggle = async (nextEnabled: boolean) => {
    setError(null);
    setLoading(true);

    try {
      const result = await onToggle(nextEnabled);
      if (!result.success) {
        setError(result.error || t('tun.toggleFail'));
      }
    } catch (err) {
      console.error('Toggle error:', err);
      setError(t('common.netErr'));
    } finally {
      setLoading(false);
    }
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
        <span style={{ fontSize: '14px', fontWeight: 600, color: '#c7d5e0' }}>
          {t('tun.title')}
        </span>
        <HelpPopover label={t('tun.help')} topic="options.tun_mode" />
      </div>

      <div style={{ marginBottom: '15px' }}>
        <Field
          label={t('tun.enable')}
          description={<span style={leftDescriptionStyle}>{t('tun.enableDesc')}</span>}
          bottomSeparator="none"
          highlightOnFocus
          childrenLayout="inline"
        >
          <Toggle
            value={enabled}
            disabled={loading || !hasPrivileges || checkingPrivileges}
            onChange={handleToggle}
          />
        </Field>

        {!hasPrivileges && (
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
            <p>
              <strong>{t('tun.privReqLabel')}</strong> {t('tun.privReqMsg')}
            </p>
            <p style={{ marginTop: '5px' }}>{t('tun.privSteps')}</p>
            <DialogButton
              onClick={handleCheckPrivileges}
              disabled={checkingPrivileges}
              style={{ width: '100%' }}
            >
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                <FaShieldAlt />
                {checkingPrivileges ? t('tun.checking') : t('tun.checkPriv')}
              </span>
            </DialogButton>
          </div>
        )}

        {hasPrivileges && enabled && (
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
              <strong>{t('tun.enabled')}</strong>
            </p>
            {isActive && tunInterface && (
              <p style={{ marginTop: '5px' }}>{t('tun.activeOn', { iface: tunInterface })}</p>
            )}
            {!isActive && <p style={{ marginTop: '5px' }}>{t('tun.connectToActivate')}</p>}
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
            {enabled ? t('tun.disabling') : t('tun.enabling')}
          </div>
        )}
      </div>
    </div>
  );
};
