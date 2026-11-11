import { Field, Toggle } from '@decky/ui';
import { useEffect, useState } from 'react';
import {
  getConnectionPreferences,
  setConnectionPreference,
  type ConnectionPreferences as Preferences,
} from '../services/api';
import { t } from '../utils/i18n';

export function ConnectionPreferences() {
  const [preferences, setPreferences] = useState<Preferences | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getConnectionPreferences()
      .then((result) => {
        if (active) setPreferences(result);
      })
      .catch(() => {
        if (active) setError(t('common.netErr'));
      });
    return () => {
      active = false;
    };
  }, []);

  const change = async (name: keyof Preferences, enabled: boolean) => {
    setError(null);
    setSaving(true);
    try {
      const result = await setConnectionPreference(name, enabled);
      if (result.success) {
        setPreferences((previous) => (previous ? { ...previous, [name]: enabled } : previous));
      } else {
        setError(result.error ?? t('common.netErr'));
      }
    } catch {
      setError(t('common.netErr'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <Field label={t('options.autoConnect')} description={t('options.autoConnectDesc')}>
        <Toggle
          value={preferences?.autoConnect ?? false}
          disabled={!preferences || saving}
          onChange={(value) => change('autoConnect', value)}
        />
      </Field>
      <Field label={t('options.steamDirect')} description={t('options.steamDirectDesc')}>
        <Toggle
          value={preferences?.steamDirect ?? false}
          disabled={!preferences || saving}
          onChange={(value) => change('steamDirect', value)}
        />
      </Field>
      {error && <div role="alert">{error}</div>}
    </>
  );
}
