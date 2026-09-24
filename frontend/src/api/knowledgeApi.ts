import { request } from "./client";
import type { Item, QueryResult, SourceType } from "./types";

export function ingestItem(sourceType: SourceType, content: string): Promise<{ item: Item }> {
  return request("/ingest", {
    method: "POST",
    body: JSON.stringify({ source_type: sourceType, content }),
  });
}

export function fetchItems(): Promise<{ items: Item[] }> {
  return request("/items");
}

export function askQuestion(question: string): Promise<QueryResult> {
  return request("/query", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}
