import { FC } from 'react';
import { ButtonItem, TextField } from '@decky/ui';
import { FaSave } from 'react-icons/fa';
import { HelpPopover } from './ui/HelpPopover';
import type { HelpTopic } from '../types/ui';

interface ConfigImportProps {
  value: string;
  onChange: (value: string) => void;
  onSave: () => void;
  isSaving: boolean;
  error?: string | null;
  successMessage?: string | null;
  helpTopic?: HelpTopic;
}

export const ConfigImport: FC<ConfigImportProps> = ({
  value,
  onChange,
  onSave,
  isSaving,
  error,
  successMessage,
  helpTopic,
}) => {
  const labelText = isSaving ? 'Saving…' : 'Save configuration';
  const leftDescriptionStyle = { display: 'block', textAlign: 'left' } as const;

  return (
    <div>
      <TextField
        label="Share link"
        description={
          <span style={leftDescriptionStyle}>
            Paste a vless://, vmess://, trojan:// or ss:// link. We validate it before saving.
          </span>
        }
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={isSaving}
        bShowClearAction
        inlineControls={
          helpTopic ? <HelpPopover label="Help: share link" topic={helpTopic} /> : undefined
        }
      />

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

      {successMessage && (
        <div
          style={{
            marginTop: '10px',
            padding: '10px',
            backgroundColor: '#1e5f1e',
            color: '#6bff6b',
            borderRadius: '5px',
          }}
        >
          <strong>Success:</strong> {successMessage}
        </div>
      )}

      <div style={{ marginTop: '10px' }}>
        <ButtonItem
          icon={<FaSave />}
          description={
            <span style={leftDescriptionStyle}>
              Save the VLESS link and switch to the configured layout.
            </span>
          }
          onClick={onSave}
          disabled={isSaving || !value.trim()}
        >
          {labelText}
        </ButtonItem>
      </div>
    </div>
  );
};
