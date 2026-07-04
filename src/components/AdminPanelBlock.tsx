import { FC, useEffect, useState } from 'react';
import { Focusable } from '@decky/ui';
import { QRCodeSVG } from 'qrcode.react';
import { AdminPanelUrlResponse, getAdminPanelUrl } from '../services/api';
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

export const AdminPanelBlock: FC<AdminPanelBlockProps> = ({ helpTopic }) => {
  const [urlInfo, setUrlInfo] = useState<AdminPanelUrlResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const fetchUrl = async () => {
      try {
        const res = await getAdminPanelUrl();
        if (!cancelled) {
          setUrlInfo(res);
          setError(null);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          const errMsg = err instanceof Error ? err.message : String(err);
          setError(errMsg);
          setUrlInfo(null);
        }
      }
    };

    fetchUrl();

    return () => {
      cancelled = true;
    };
  }, []);

  const header = (
    <div style={headerRowStyle}>
      <span style={headerLabelStyle}>{t('admin.title')}</span>
      {helpTopic && <HelpPopover label={t('admin.help')} topic={helpTopic} />}
    </div>
  );

  if (error) {
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

  const adminUrl =
    urlInfo.baseUrl.replace(/\/$/, '') +
    urlInfo.path +
    '?token=' +
    encodeURIComponent(urlInfo.token);

  return (
    <div>
      {header}
      <p style={{ color: '#8f98a0', marginBottom: '12px' }}>{t('admin.desc')}</p>

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
