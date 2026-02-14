import { FC, useState } from 'react';
import { ButtonItem } from '@decky/ui';
import { FaUndoAlt } from 'react-icons/fa';

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

  const labelText = loading ? 'Resetting…' : 'Reset configuration';
  const description = disabled
    ? 'Disconnect before resetting configuration.'
    : 'Clears the saved VLESS link and returns to setup.';

  const handleReset = async () => {
    setError(null);
    setLoading(true);
    try {
      const result = await onReset();
      if (!result.success) {
        setError(result.error || 'Failed to reset configuration');
      }
    } catch (err) {
      console.error('Reset error:', err);
      setError('Network error. Please try again.');
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
          <strong>Error:</strong> {error}
        </div>
      )}
    </div>
  );
};
