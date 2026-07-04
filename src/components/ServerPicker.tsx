import { FC, useCallback, useEffect, useState } from 'react';
import { Dropdown, Field, Focusable, showContextMenu, Menu, MenuItem } from '@decky/ui';
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

  const load = useCallback(async () => {
    try {
      const result = await getProfiles();
      if (result.success) {
        setProfiles(result.profiles || []);
        setActiveId(result.activeId ?? null);
      }
    } catch {
      /* transient */
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- load() fetches profiles; setState runs in its async callback
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
        setBusy(false);
        void load();
      }
    },
    [activeId, busy, load]
  );

  const handlePing = useCallback(async () => {
    if (busy) return;
    setBusy(true);
    try {
      await testProfilesLatency();
    } finally {
      setBusy(false);
      void load();
    }
  }, [busy, load]);

  // Only worth showing a picker when there is more than one server.
  if (profiles.length < 2) {
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

  const openMenu = () => {
    showContextMenu(
      <Menu label={t('servers.menuLabel')}>
        {profiles.map((profile) => (
          <MenuItem key={profile.id} onSelected={() => void handleSelect(profile.id)}>
            <span style={rowStyle}>
              <span>{profileLabel(profile)}</span>
              <span style={{ color: latencyColor(profile.latencyMs) }}>{latencyText(profile)}</span>
            </span>
          </MenuItem>
        ))}
        <MenuItem onSelected={() => void handlePing()}>{t('servers.pingAll')}</MenuItem>
      </Menu>
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
      <Focusable onSecondaryButton={openMenu} onMenuButton={openMenu}>
        <Dropdown
          rgOptions={dropdownOptions}
          selectedOption={activeId ?? undefined}
          onChange={(option) => void handleSelect(option.data as string)}
          disabled={busy}
          strDefaultLabel={t('servers.select')}
        />
      </Focusable>
      <Field
        bottomSeparator="none"
        description={
          <span style={{ fontSize: '12px', color: '#8f98a0' }}>{t('servers.pingHint')}</span>
        }
      />
    </div>
  );
};
