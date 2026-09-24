import type { Item } from "../api/types";

interface Props {
  items: Item[];
  loading: boolean;
  error: string | null;
}

export function ItemList({ items, loading, error }: Props) {
  if (loading) return <p className="text-sm text-slate-500">Loading items...</p>;
  if (error) return <p className="text-sm text-red-600">{error}</p>;
  if (items.length === 0) return <p className="text-sm text-slate-500">No items saved yet.</p>;

  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li key={item.id} className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="uppercase tracking-wide">{item.source_type}</span>
            <span>{new Date(item.created_at).toLocaleString()}</span>
          </div>
          {item.source_url && (
            <a
              href={item.source_url}
              target="_blank"
              rel="noreferrer"
              className="block truncate text-blue-600 underline"
            >
              {item.source_url}
            </a>
          )}
          <p className="mt-1 text-slate-700">{item.content_preview}</p>
          <p className="mt-1 text-xs text-slate-400">{item.chunk_count} chunk(s)</p>
        </li>
      ))}
    </ul>
  );
}
