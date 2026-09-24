import { request } from "./client";
import type { RuntimeSettings } from "./types";

export function fetchSettings(): Promise<RuntimeSettings> {
  return request("/settings");
}

export function updateSettings(patch: Partial<RuntimeSettings>): Promise<RuntimeSettings> {
  return request("/settings", {
    method: "PUT",
    body: JSON.stringify(patch),
  });
}
