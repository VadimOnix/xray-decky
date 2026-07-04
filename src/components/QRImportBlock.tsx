import { FC, useEffect, useState } from 'react';
import { Focusable } from '@decky/ui';
import { QRCodeSVG } from 'qrcode.react';
import { getImportServerUrl, ImportServerUrlResponse } from '../services/api';
import { HelpPopover } from './ui/HelpPopover';
import type { HelpTopic } from '../types/ui';
import { t } from '../utils/i18n';

interface QRImportBlockProps {
  helpTopicQr?: HelpTopic;
  helpTopicLan?: HelpTopic;
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

export const QRImportBlock: FC<QRImportBlockProps> = ({ helpTopicQr, helpTopicLan }) => {
  const [urlInfo, setUrlInfo] = useState<ImportServerUrlResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const fetchUrl = async () => {
      try {
        const res = await getImportServerUrl();
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

  if (error) {
    return (
      <div>
        <div style={headerRowStyle}>
          <span style={headerLabelStyle}>{t('qr.title')}</span>
          {helpTopicQr && <HelpPopover label={t('qr.help')} topic={helpTopicQr} />}
        </div>
        <p style={{ color: '#ff6b6b', marginTop: '8px' }}>{error}</p>
      </div>
    );
  }

  if (!urlInfo) {
    return (
      <div>
        <div style={headerRowStyle}>
          <span style={headerLabelStyle}>{t('qr.title')}</span>
          {helpTopicQr && <HelpPopover label={t('qr.help')} topic={helpTopicQr} />}
        </div>
        <p style={{ color: '#8f98a0', marginTop: '8px' }}>{t('qr.loading')}</p>
      </div>
    );
  }

  const importUrl = urlInfo.baseUrl.replace(/\/$/, '') + urlInfo.path;

  return (
    <div>
      <div style={headerRowStyle}>
        <span style={headerLabelStyle}>{t('qr.title')}</span>
        {helpTopicQr && <HelpPopover label={t('qr.help')} topic={helpTopicQr} />}
      </div>
      <p style={{ color: '#8f98a0', marginBottom: '12px' }}>{t('qr.desc')}</p>

      {/* QR code section */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '12px',
        }}
      >
        <QRCodeSVG value={importUrl} size={180} level="M" />
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
          <div style={headerRowStyle}>
            <span style={{ fontSize: '14px', color: '#c7d5e0' }}>{t('qr.importUrl')}</span>
            {helpTopicLan && <HelpPopover label={t('qr.helpLan')} topic={helpTopicLan} />}
          </div>
          <p
            style={{
              fontSize: '14px',
              color: '#66c0f4',
              wordBreak: 'break-all',
              fontFamily: 'monospace',
            }}
          >
            {importUrl}
          </p>
        </div>
      </Focusable>
    </div>
  );
};
