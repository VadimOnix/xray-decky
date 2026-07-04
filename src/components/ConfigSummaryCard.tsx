import { FC } from 'react';
import { Field } from '@decky/ui';
import type { ConnectionConfigSummary } from '../types/ui';
import { t } from '../utils/i18n';

interface ConfigSummaryCardProps {
  summary: ConnectionConfigSummary;
}

export const ConfigSummaryCard: FC<ConfigSummaryCardProps> = ({ summary }) => {
  if (!summary.exists) {
    return null;
  }

  const statusText = summary.isValid ? t('summary.valid') : t('summary.invalid');
  const leftDescriptionStyle = { display: 'block', textAlign: 'left' } as const;
  const cardStyle = {
    padding: '10px',
    backgroundColor: '#1e3a5f',
    borderRadius: '6px',
  };

  return (
    <div style={cardStyle}>
      {summary.displayName && (
        <Field
          label={t('summary.name')}
          bottomSeparator="none"
          description={<span style={leftDescriptionStyle}>{summary.displayName}</span>}
        />
      )}
      {summary.endpoint && (
        <Field
          label={t('summary.endpoint')}
          bottomSeparator="none"
          description={<span style={leftDescriptionStyle}>{summary.endpoint}</span>}
        />
      )}
      <Field
        label={t('summary.status')}
        bottomSeparator="none"
        description={<span style={leftDescriptionStyle}>{statusText}</span>}
      />
      {summary.validationError && (
        <Field
          label={t('summary.validationError')}
          bottomSeparator="none"
          description={
            <span style={{ ...leftDescriptionStyle, color: '#ff6b6b' }}>
              {summary.validationError}
            </span>
          }
        />
      )}
      {summary.source && (
        <Field
          label={t('summary.source')}
          bottomSeparator="none"
          description={<span style={leftDescriptionStyle}>{summary.source}</span>}
        />
      )}
    </div>
  );
};
