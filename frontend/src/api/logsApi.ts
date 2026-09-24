import { request } from "./client";
import type { LogEntry } from "./types";

export function fetchLogs(limit = 100, level?: string): Promise<{ logs: LogEntry[] }> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (level) params.set("level", level);
  return request(`/logs?${params.toString()}`);
}
