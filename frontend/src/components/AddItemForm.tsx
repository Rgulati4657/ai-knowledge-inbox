import { useState } from "react";
import { ingestItem } from "../api/knowledgeApi";
import type { SourceType } from "../api/types";

interface Props {
  onAdded: () => void;
}

export function AddItemForm({ onAdded }: Props) {
  const [sourceType, setSourceType] = useState<SourceType>("note");
  const [content, setContent] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!content.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      await ingestItem(sourceType, content.trim());
      setContent("");
      onAdded();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add item");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex gap-4">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="radio"
            checked={sourceType === "note"}
            onChange={() => setSourceType("note")}
          />
          Note
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="radio"
            checked={sourceType === "url"}
            onChange={() => setSourceType("url")}
          />
          URL
        </label>
      </div>

      {sourceType === "note" ? (
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Paste or type a note..."
          rows={4}
          className="w-full rounded-md border border-slate-300 p-2 text-sm"
        />
      ) : (
        <input
          type="url"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="https://example.com/article"
          className="w-full rounded-md border border-slate-300 p-2 text-sm"
        />
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        type="submit"
        disabled={submitting || !content.trim()}
        className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitting ? "Adding..." : "Add"}
      </button>
    </form>
  );
}
