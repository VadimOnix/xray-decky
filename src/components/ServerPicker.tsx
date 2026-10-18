import { FC, type CSSProperties, useCallback, useEffect, useState } from 'react';
import { DialogButton, Dropdown, Focusable, showContextMenu, Menu, MenuItem } from '@decky/ui';
import {
  getProfiles,
  setActiveProfile,
  testProfilesLatency,
  type ServerProfile,
} from '../services/api';
import { t } from '../utils/i18n';

interface ServerPickerProps {
  /** Bumped by the parent whenever the config changes, to trigger a refetch. */
  refreshKey?: number;
}

const rowStyle = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: '8px',
};

const labelStyle = {
  fontSize: '14px',
  fontWeight: 600,
  color: '#c7d5e0',
};

const buttonStyle: CSSProperties = {
  flex: '1 1 0',
  minWidth: 0,
  minHeight: '44px',
  height: 'auto',
  margin: 0,
  padding: '8px',
  boxSizing: 'border-box',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
};

const latencyColor = (ms?: number | null): string => {
  if (ms == null) return '#8f98a0';
  if (ms < 150) return '#a1cd44';
  if (ms < 400) return '#f5a623';
  return '#ff7a5c';
};

const latencyText = (profile: ServerProfile): string => {
  if (typeof profile.latencyMs === 'number') return `${profile.latencyMs} ms`;
  if (profile.latencyTestedAt) return t('servers.offline');
  return '— ms';
};

const profileLabel = (profile: ServerProfile): string =>
  profile.name || profile.address || t('servers.unnamed');

export const ServerPicker: FC<ServerPickerProps> = ({ refreshKey }) => {
  const [profiles, setProfiles] = useState<ServerProfile[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const result = await getProfiles();
      if (result.success) {
        setProfiles(result.profiles || []);
        setActiveId(result.activeId ?? null);
        return true;
      }
    } catch {
      /* transient */
    }
    return false;
  }, []);

  useEffect(() => {
    // load() fetches profiles; setState runs in its async callback
    void load();
  }, [load, refreshKey]);

  const handleSelect = useCallback(
    async (profileId: string) => {
      if (profileId === activeId || busy) return;
      setBusy(true);
      setActiveId(profileId); // optimistic
      try {
        await setActiveProfile(profileId);
      } finally {
        await load();
        setBusy(false);
      }
    },
    [activeId, busy, load]
  );

  const handlePing = useCallback(
    async (profileId?: string) => {
      if (busy) return;
      setBusy(true);
      setError(null);
      try {
        const result =
          profileId === undefined
            ? await testProfilesLatency()
            : await testProfilesLatency(profileId);
        if (!result.success) {
          setError(result.error || t('servers.pingFailed'));
        }
      } catch {
        setError(t('servers.pingFailed'));
      } finally {
        if (!(await load())) {
          setError((current) => current ?? t('servers.refreshFailed'));
        }
        setBusy(false);
      }
    },
    [busy, load]
  );

  if (profiles.length === 0) {
    return null;
  }

  const activeProfile = profiles.find((p) => p.id === activeId);

  const dropdownOptions = profiles.map((profile) => ({
    data: profile.id,
    label: (
      <span style={rowStyle}>
        <span
          style={{
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {profileLabel(profile)}
        </span>
        <span style={{ color: latencyColor(profile.latencyMs), fontVariant: 'tabular-nums' }}>
          {latencyText(profile)}
        </span>
      </span>
    ),
  }));

  // Render refreshed labels instead of Steam's cached selected option.
  const activeOption = dropdownOptions.find((option) => option.data === activeId);

  const openPingMenu = (event: MouseEvent) => {
    if (busy) return;
    showContextMenu(
      <Menu label={t('servers.pingSelect')}>
        {dropdownOptions.map((option) => (
          <MenuItem key={option.data} onSelected={() => void handlePing(option.data)}>
            {option.label}
          </MenuItem>
        ))}
      </Menu>,
      event.currentTarget ?? undefined
    );
  };

  return (
    <div style={{ marginBottom: '8px' }}>
      <div style={{ ...rowStyle, marginBottom: '6px' }}>
        <span style={labelStyle}>{t('servers.server')}</span>
        {activeProfile && (
          <span
            style={{
              fontSize: '13px',
              color: latencyColor(activeProfile.latencyMs),
              fontVariant: 'tabular-nums',
            }}
          >
            {latencyText(activeProfile)}
          </span>
        )}
      </div>
      <Dropdown
        rgOptions={dropdownOptions}
        selectedOption={activeId ?? undefined}
        renderButtonValue={() => activeOption?.label ?? t('servers.select')}
        onChange={(option) => void handleSelect(option.data as string)}
        disabled={busy}
        strDefaultLabel={t('servers.select')}
      />
      <Focusable
        flow-children="right"
        style={{ ...rowStyle, alignItems: 'stretch', marginTop: '8px' }}
      >
        <DialogButton style={buttonStyle} disabled={busy} onClick={openPingMenu}>
          {t('servers.ping')}
        </DialogButton>
        <DialogButton style={buttonStyle} disabled={busy} onClick={() => void handlePing()}>
          {t('servers.pingAll')}
        </DialogButton>
      </Focusable>
      {error && (
        <div role="alert" style={{ marginTop: '8px', color: '#ff7a5c', fontSize: '13px' }}>
          <strong>{t('common.errorLabel')}</strong> {error}
        </div>
      )}
    </div>
  );
};
