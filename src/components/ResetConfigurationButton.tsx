import { FC, useState } from 'react';
import { ButtonItem } from '@decky/ui';
import { FaUndoAlt } from 'react-icons/fa';
import { t } from '../utils/i18n';

interface ResetConfigurationButtonProps {
  disabled: boolean;
  onReset: () => Promise<{ success: boolean; error?: string }>;
}

export const ResetConfigurationButton: FC<ResetConfigurationButtonProps> = ({
  disabled,
  onReset,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const leftDescriptionStyle = { display: 'block', textAlign: 'left' } as const;

  const labelText = loading ? t('reset.resetting') : t('reset.reset');
  const description = disabled ? t('reset.disabledDesc') : t('reset.desc');

  const handleReset = async () => {
    setError(null);
    setLoading(true);
    try {
      const result = await onReset();
      if (!result.success) {
        setError(result.error || t('reset.fail'));
      }
    } catch (err) {
      console.error('Reset error:', err);
      setError(t('reset.netErr'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <ButtonItem
        layout="inline"
        icon={<FaUndoAlt />}
        description={<span style={leftDescriptionStyle}>{description}</span>}
        onClick={handleReset}
        disabled={disabled || loading}
      >
        {labelText}
      </ButtonItem>
      {error && (
        <div
          style={{
            marginTop: '10px',
            padding: '10px',
            backgroundColor: '#5f1e1e',
            color: '#ff6b6b',
            borderRadius: '5px',
          }}
        >
          <strong>{t('common.errorLabel')}</strong> {error}
        </div>
      )}
    </div>
  );
};
