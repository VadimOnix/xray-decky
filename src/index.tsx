import { definePlugin } from '@decky/api';
import { handleResume } from './services/api';
import { ErrorBoundary } from '@decky/ui';
import { FaNetworkWired } from 'react-icons/fa';
import { useState } from 'react';
import { ConfiguredLayout } from './components/layouts/ConfiguredLayout';
import { SetupLayout } from './components/layouts/SetupLayout';
import { usePluginPanelState } from './hooks/usePluginPanelState';

function SetupContent({ saveConfig }: Pick<ReturnType<typeof usePluginPanelState>, 'saveConfig'>) {
  const [vlessUrl, setVlessUrl] = useState('');
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

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

  return (
    <SetupLayout
      vlessUrl={vlessUrl}
      onVlessUrlChange={setVlessUrl}
      onSave={handleSave}
      isSaving={isSaving}
      error={saveError}
      successMessage={saveSuccess}
    />
  );
}

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

  if (isLoading && layout === 'setup') {
    return <div style={{ padding: '10px', color: '#8f98a0' }}>Loading…</div>;
  }

  if (layout === 'setup') return <SetupContent saveConfig={saveConfig} />;

  return (
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
  );
}

// New Decky API: definePlugin takes no arguments
// https://wiki.deckbrew.xyz/en/plugin-dev/new-api-migration
export default definePlugin(() => {
  console.log('Xray Decky plugin initializing');

  // Suspend/resume is a top failure source for proxying on the Deck: the
  // TUN default route can vanish while xray-core keeps running. Let the
  // backend repair routing every time the device wakes up.
  const resumeRegistration = SteamClient?.System?.RegisterForOnResumeFromSuspend?.(() => {
    handleResume().catch((err) => console.error('Xray Decky: resume handling failed', err));
  });

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
      resumeRegistration?.unregister();
    },
  };
});
