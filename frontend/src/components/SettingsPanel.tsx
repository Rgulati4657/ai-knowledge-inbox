import { useEffect, useState } from "react";
import { useSettings } from "../hooks/useSettings";
import type { RuntimeSettings } from "../api/types";

export function SettingsPanel() {
  const { settings, loading, saving, error, save } = useSettings();
  const [draft, setDraft] = useState<RuntimeSettings | null>(null);
  const [savedMessage, setSavedMessage] = useState(false);

  useEffect(() => {
    if (settings) setDraft(settings);
  }, [settings]);

  if (loading || !draft) return <p className="text-sm text-slate-500">Loading settings...</p>;

  async function handleSave() {
    if (!draft) return;
    const ok = await save(draft);
    setSavedMessage(ok);
    if (ok) setTimeout(() => setSavedMessage(false), 2000);
  }

  return (
    <div className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
      <div>
        <h3 className="text-sm font-medium text-slate-800">Providers</h3>
        <p className="mb-2 text-xs text-slate-500">
          API keys live only in the server's .env file and cannot be viewed or changed here.
        </p>
        <div className="flex gap-4">
          <label className="flex-1 text-xs text-slate-600">
            Embedding provider
            <select
              value={draft.embedding_provider}
              onChange={(e) => setDraft({ ...draft, embedding_provider: e.target.value as RuntimeSettings["embedding_provider"] })}
              className="mt-1 w-full rounded-md border border-slate-300 p-2 text-sm"
            >
              <option value="gemini">gemini</option>
              <option value="local">local (sentence-transformers)</option>
            </select>
          </label>
          <label className="flex-1 text-xs text-slate-600">
            Generation provider
            <select
              value={draft.generation_provider}
              onChange={(e) => setDraft({ ...draft, generation_provider: e.target.value as RuntimeSettings["generation_provider"] })}
              className="mt-1 w-full rounded-md border border-slate-300 p-2 text-sm"
            >
              <option value="gemini">gemini</option>
              <option value="groq">groq</option>
              <option value="local">local (Ollama)</option>
            </select>
          </label>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-medium text-slate-800">Chunking &amp; retrieval</h3>
        <p className="mb-2 text-xs text-slate-500">
          Chunk size/overlap only affect items ingested after saving - existing items keep the chunks they were created with.
        </p>
        <div className="flex gap-4">
          <label className="flex-1 text-xs text-slate-600">
            Chunk size (chars)
            <input
              type="number"
              min={50}
              value={draft.chunk_size_chars}
              onChange={(e) => setDraft({ ...draft, chunk_size_chars: Number(e.target.value) })}
              className="mt-1 w-full rounded-md border border-slate-300 p-2 text-sm"
            />
          </label>
          <label className="flex-1 text-xs text-slate-600">
            Overlap (chars)
            <input
              type="number"
              min={0}
              value={draft.chunk_overlap_chars}
              onChange={(e) => setDraft({ ...draft, chunk_overlap_chars: Number(e.target.value) })}
              className="mt-1 w-full rounded-md border border-slate-300 p-2 text-sm"
            />
          </label>
          <label className="flex-1 text-xs text-slate-600">
            Top K (retrieved chunks)
            <input
              type="number"
              min={1}
              max={20}
              value={draft.top_k}
              onChange={(e) => setDraft({ ...draft, top_k: Number(e.target.value) })}
              className="mt-1 w-full rounded-md border border-slate-300 p-2 text-sm"
            />
          </label>
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {savedMessage && <p className="text-sm text-green-600">Saved.</p>}

      <button
        onClick={handleSave}
        disabled={saving}
        className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {saving ? "Saving..." : "Save settings"}
      </button>
    </div>
  );
}
