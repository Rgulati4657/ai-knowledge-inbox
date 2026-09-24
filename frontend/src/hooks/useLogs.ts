import { useCallback, useEffect, useState } from "react";
import { fetchLogs } from "../api/logsApi";
import type { LogEntry } from "../api/types";

const POLL_INTERVAL_MS = 4000;

export function useLogs(level?: string) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const { logs } = await fetchLogs(200, level);
      setLogs(logs);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load logs");
    }
  }, [level]);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [refresh]);

  return { logs, error, refresh };
}
