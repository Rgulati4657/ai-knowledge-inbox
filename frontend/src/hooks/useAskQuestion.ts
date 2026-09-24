import { useCallback, useState } from "react";
import { askQuestion } from "../api/knowledgeApi";
import type { QueryResult } from "../api/types";

export function useAskQuestion() {
  const [result, setResult] = useState<QueryResult | null>(null);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ask = useCallback(async (question: string) => {
    setAsking(true);
    setError(null);
    try {
      const res = await askQuestion(question);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get an answer");
      setResult(null);
    } finally {
      setAsking(false);
    }
  }, []);

  return { result, asking, error, ask };
}
