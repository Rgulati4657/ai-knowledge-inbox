import { useState } from "react";
import { useLogs } from "../hooks/useLogs";

const LEVEL_COLORS: Record<string, string> = {
  INFO: "text-slate-600",
  WARNING: "text-amber-600",
  ERROR: "text-red-600",
  CRITICAL: "text-red-700",
};

export function LogsPanel() {
  const [level, setLevel] = useState<string>("");
  const { logs, error, refresh } = useLogs(level || undefined);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <select
          value={level}
          onChange={(e) => setLevel(e.target.value)}
          className="rounded-md border border-slate-300 p-1.5 text-xs"
        >
          <option value="">All levels</option>
          <option value="INFO">INFO</option>
          <option value="WARNING">WARNING</option>
          <option value="ERROR">ERROR</option>
        </select>
        <button onClick={refresh} className="text-xs text-slate-500 underline">
          Refresh now
        </button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="max-h-96 overflow-y-auto rounded-lg border border-slate-200 bg-white">
        {logs.length === 0 ? (
          <p className="p-3 text-sm text-slate-500">No log entries yet.</p>
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="sticky top-0 bg-slate-50 text-slate-400">
              <tr>
                <th className="px-3 py-2">Time</th>
                <th className="px-3 py-2">Level</th>
                <th className="px-3 py-2">Logger</th>
                <th className="px-3 py-2">Message</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log, i) => (
                <tr key={i} className="border-t border-slate-100">
                  <td className="whitespace-nowrap px-3 py-1.5 text-slate-400">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </td>
                  <td className={`px-3 py-1.5 font-medium ${LEVEL_COLORS[log.level] ?? "text-slate-600"}`}>
                    {log.level}
                  </td>
                  <td className="px-3 py-1.5 text-slate-400">{log.logger}</td>
                  <td className="px-3 py-1.5 text-slate-700">{log.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
