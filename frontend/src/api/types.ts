export type SourceType = "note" | "url";

export interface Item {
  id: number;
  source_type: SourceType;
  source_url: string | null;
  content_preview: string;
  chunk_count: number;
  created_at: string;
}

export interface SourceSnippet {
  item_id: number;
  source_type: SourceType;
  source_url: string | null;
  snippet: string;
  similarity: number;
}

export interface QueryResult {
  answer: string;
  sources: SourceSnippet[];
}

export interface RuntimeSettings {
  embedding_provider: "gemini" | "local";
  generation_provider: "gemini" | "groq" | "local";
  chunk_size_chars: number;
  chunk_overlap_chars: number;
  top_k: number;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  logger: string;
  message: string;
}
