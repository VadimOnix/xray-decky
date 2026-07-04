import { FC, useCallback, useEffect, useState } from 'react';
import { Field, Focusable, Toggle } from '@decky/ui';
import { QRCodeSVG } from 'qrcode.react';
import { AdminPanelUrlResponse, getAdminPanelUrl, setLanAccess } from '../services/api';
import { HelpPopover } from './ui/HelpPopover';
import type { HelpTopic } from '../types/ui';
import { t } from '../utils/i18n';

interface AdminPanelBlockProps {
  helpTopic?: HelpTopic;
}

const headerRowStyle = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: '8px',
};

const headerLabelStyle = {
  fontSize: '14px',
  fontWeight: 600,
  color: '#c7d5e0',
};

const leftDescriptionStyle = { display: 'block', textAlign: 'left' } as const;

export const AdminPanelBlock: FC<AdminPanelBlockProps> = ({ helpTopic }) => {
  const [urlInfo, setUrlInfo] = useState<AdminPanelUrlResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lanBusy, setLanBusy] = useState(false);

  const fetchUrl = useCallback(async () => {
    try {
      const res = await getAdminPanelUrl();
      setUrlInfo(res);
      setError(null);
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      setError(errMsg);
      setUrlInfo(null);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      if (!cancelled) await fetchUrl();
    };
    load();

    return () => {
      cancelled = true;
    };
  }, [fetchUrl]);

  const handleLanToggle = async (enabled: boolean) => {
    setLanBusy(true);
    setError(null);
    try {
      const res = await setLanAccess(enabled);
      if (!res.success) {
        setError(res.error || t('admin.lanFail'));
      }
      // The URL/QR flips between the LAN IP and 127.0.0.1 — refresh it.
      await fetchUrl();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('admin.lanFail'));
    } finally {
      setLanBusy(false);
    }
  };

  const header = (
    <div style={headerRowStyle}>
      <span style={headerLabelStyle}>{t('admin.title')}</span>
      {helpTopic && <HelpPopover label={t('admin.help')} topic={helpTopic} />}
    </div>
  );

  if (error && !urlInfo) {
    return (
      <div>
        {header}
        <p style={{ color: '#ff6b6b', marginTop: '8px' }}>{error}</p>
      </div>
    );
  }

  if (!urlInfo) {
    return (
      <div>
        {header}
        <p style={{ color: '#8f98a0', marginTop: '8px' }}>{t('admin.loading')}</p>
      </div>
    );
  }

  const lanAllowed = urlInfo.allowLan !== false;
  const adminUrl =
    urlInfo.baseUrl.replace(/\/$/, '') +
    urlInfo.path +
    '?token=' +
    encodeURIComponent(urlInfo.token);

  return (
    <div>
      {header}
      <p style={{ color: '#8f98a0', marginBottom: '12px' }}>{t('admin.desc')}</p>

      <Field
        label={t('admin.lan')}
        description={<span style={leftDescriptionStyle}>{t('admin.lanDesc')}</span>}
        bottomSeparator="none"
        highlightOnFocus
        childrenLayout="inline"
      >
        <Toggle value={lanAllowed} disabled={lanBusy} onChange={handleLanToggle} />
      </Field>

      {error && <p style={{ color: '#ff6b6b', marginBottom: '8px' }}>{error}</p>}

      {!lanAllowed && (
        <p style={{ color: '#e8b339', marginBottom: '12px', fontSize: '13px' }}>
          {t('admin.lanOffNote')}
        </p>
      )}

      {lanAllowed && (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '12px',
          }}
        >
          <QRCodeSVG value={adminUrl} size={180} level="M" />
        </div>
      )}

      <Focusable>
        <div
          style={{
            marginBottom: '12px',
            padding: '10px',
            backgroundColor: '#1e3a5f',
            borderRadius: '5px',
          }}
        >
          <span style={{ fontSize: '14px', color: '#c7d5e0' }}>{t('admin.url')}</span>
          <p
            style={{
              fontSize: '14px',
              color: '#66c0f4',
              wordBreak: 'break-all',
              fontFamily: 'monospace',
            }}
          >
            {adminUrl}
          </p>
        </div>
      </Focusable>
    </div>
  );
};
