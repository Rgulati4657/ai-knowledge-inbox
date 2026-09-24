import { useState } from "react";
import Markdown from "react-markdown";
import { useAskQuestion } from "../hooks/useAskQuestion";

// react-markdown renders to React elements (no dangerouslySetInnerHTML) and
// does not interpret raw HTML in the source by default, so it's safe to
// point straight at LLM output even though that text is untrusted.
const MARKDOWN_CLASSES =
  "text-sm text-slate-800 [&_p]:my-1.5 [&_ul]:my-1.5 [&_ul]:list-disc [&_ul]:pl-5 " +
  "[&_ol]:my-1.5 [&_ol]:list-decimal [&_ol]:pl-5 [&_strong]:font-semibold " +
  "[&_code]:rounded [&_code]:bg-slate-100 [&_code]:px-1 [&_code]:py-0.5 [&_code]:text-xs " +
  "[&_a]:text-blue-600 [&_a]:underline";

export function AskQuestion() {
  const [question, setQuestion] = useState("");
  const { result, asking, error, ask } = useAskQuestion();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    ask(question.trim());
  }

  return (
    <div className="space-y-3">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about your saved content..."
          className="flex-1 rounded-md border border-slate-300 p-2 text-sm"
        />
        <button
          type="submit"
          disabled={asking || !question.trim()}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {asking ? "Thinking..." : "Ask"}
        </button>
      </form>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {result && (
        <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
          <div className={MARKDOWN_CLASSES}>
            <Markdown>{result.answer}</Markdown>
          </div>

          {result.sources.length > 0 && (
            <div className="space-y-2 border-t border-slate-100 pt-3">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Sources</p>
              {result.sources.map((source, i) => (
                <div key={`${source.item_id}-${i}`} className="rounded-md bg-slate-50 p-2 text-xs text-slate-600">
                  <div className="mb-1 flex items-center justify-between text-slate-400">
                    <span>
                      [{i + 1}] item #{source.item_id} - {source.source_type}
                    </span>
                    <span>similarity {source.similarity.toFixed(2)}</span>
                  </div>
                  <p>{source.snippet}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
