import { definePlugin } from '@decky/api';
import { ErrorBoundary } from '@decky/ui';
import { FaNetworkWired } from 'react-icons/fa';
import { useEffect, useState } from 'react';
import { ConfiguredLayout } from './components/layouts/ConfiguredLayout';
import { SetupLayout } from './components/layouts/SetupLayout';
import { usePluginPanelState } from './hooks/usePluginPanelState';

function Content() {
  const {
    layout,
    configSummary,
    connection,
    options,
    isLoading,
    saveConfig,
    resetConfig,
    toggleConnection,
    toggleTUNMode,
    toggleKillSwitch,
    deactivateKillSwitch,
    checkTUNPrivileges,
  } = usePluginPanelState();

  const [vlessUrl, setVlessUrl] = useState('');
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (layout === 'setup') {
      setSaveError(null);
      setSaveSuccess(null);
      setVlessUrl('');
    }
  }, [layout]);

  const handleSave = async () => {
    setSaveError(null);
    setSaveSuccess(null);
    setIsSaving(true);
    try {
      const result = await saveConfig(vlessUrl);
      if (result.success) {
        setSaveSuccess('Configuration saved');
        setTimeout(() => setSaveSuccess(null), 3000);
      } else {
        setSaveError(result.error || 'Failed to save configuration');
      }
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading && layout === 'setup') {
    return <div style={{ padding: '10px', color: '#8f98a0' }}>Loading…</div>;
  }

  return (
    <>
      {layout === 'setup' ? (
        <SetupLayout
          vlessUrl={vlessUrl}
          onVlessUrlChange={setVlessUrl}
          onSave={handleSave}
          isSaving={isSaving}
          error={saveError}
          successMessage={saveSuccess}
        />
      ) : (
        <ConfiguredLayout
          configSummary={configSummary}
          connection={connection}
          options={options}
          onToggleConnection={toggleConnection}
          onToggleTUNMode={toggleTUNMode}
          onCheckTUNPrivileges={checkTUNPrivileges}
          onToggleKillSwitch={toggleKillSwitch}
          onDeactivateKillSwitch={deactivateKillSwitch}
          onResetConfig={resetConfig}
        />
      )}
    </>
  );
}

// New Decky API: definePlugin takes no arguments
// https://wiki.deckbrew.xyz/en/plugin-dev/new-api-migration
export default definePlugin(() => {
  console.log('Xray Decky plugin initializing');

  return {
    name: 'Xray Decky',
    content: (
      <ErrorBoundary>
        <Content />
      </ErrorBoundary>
    ),
    icon: <FaNetworkWired />,
    onDismount() {
      console.log('Xray Decky plugin unloading');
    },
  };
});
