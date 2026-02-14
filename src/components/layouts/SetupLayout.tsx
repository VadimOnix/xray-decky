import { FC } from 'react';
import { ConfigImport } from '../ConfigImport';
import { QRImportBlock } from '../QRImportBlock';
import { PanelSection, PanelSectionRow } from '../ui/primitives';

interface SetupLayoutProps {
  vlessUrl: string;
  onVlessUrlChange: (value: string) => void;
  onSave: () => void;
  isSaving: boolean;
  error?: string | null;
  successMessage?: string | null;
}

export const SetupLayout: FC<SetupLayoutProps> = ({
  vlessUrl,
  onVlessUrlChange,
  onSave,
  isSaving,
  error,
  successMessage,
}) => {
  return (
    <PanelSection title="Setup">
      <PanelSectionRow>
        <QRImportBlock helpTopicQr="setup.qr_import" helpTopicLan="setup.lan_address" />
      </PanelSectionRow>
      <PanelSectionRow>
        <ConfigImport
          value={vlessUrl}
          onChange={onVlessUrlChange}
          onSave={onSave}
          isSaving={isSaving}
          error={error}
          successMessage={successMessage}
          helpTopic="setup.vless_link"
        />
      </PanelSectionRow>
    </PanelSection>
  );
};
