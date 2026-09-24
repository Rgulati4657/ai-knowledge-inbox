import { useCallback, useEffect, useState } from "react";
import { fetchSettings, updateSettings } from "../api/settingsApi";
import type { RuntimeSettings } from "../api/types";

export function useSettings() {
  const [settings, setSettings] = useState<RuntimeSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setSettings(await fetchSettings());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load settings");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const save = useCallback(async (patch: Partial<RuntimeSettings>) => {
    setSaving(true);
    setError(null);
    try {
      setSettings(await updateSettings(patch));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save settings");
      return false;
    } finally {
      setSaving(false);
    }
  }, []);

  return { settings, loading, saving, error, save };
}
