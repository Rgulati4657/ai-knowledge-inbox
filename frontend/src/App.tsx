import { useState } from "react";
import { AddItemForm } from "./components/AddItemForm";
import { AskQuestion } from "./components/AskQuestion";
import { ItemList } from "./components/ItemList";
import { LogsPanel } from "./components/LogsPanel";
import { SettingsPanel } from "./components/SettingsPanel";
import { useItems } from "./hooks/useItems";

const TABS = ["Inbox", "Settings", "Logs"] as const;
type Tab = (typeof TABS)[number];

function App() {
  const [tab, setTab] = useState<Tab>("Inbox");
  const { items, loading, error, refresh } = useItems();

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">AI Knowledge Inbox</h1>
        <p className="text-sm text-slate-500">Save notes and URLs, then ask questions over them.</p>
      </header>

      <nav className="flex gap-1 border-b border-slate-200">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-2 text-sm font-medium ${
              tab === t
                ? "border-b-2 border-slate-900 text-slate-900"
                : "text-slate-400 hover:text-slate-600"
            }`}
          >
            {t}
          </button>
        ))}
      </nav>

      {tab === "Inbox" && (
        <div className="space-y-8">
          <section className="space-y-3">
            <h2 className="text-lg font-medium text-slate-800">Add content</h2>
            <AddItemForm onAdded={refresh} />
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-medium text-slate-800">Saved items</h2>
            <ItemList items={items} loading={loading} error={error} />
          </section>

          <section className="space-y-3">
            <h2 className="text-lg font-medium text-slate-800">Ask a question</h2>
            <AskQuestion />
          </section>
        </div>
      )}

      {tab === "Settings" && (
        <section className="space-y-3">
          <h2 className="text-lg font-medium text-slate-800">Runtime settings</h2>
          <SettingsPanel />
        </section>
      )}

      {tab === "Logs" && (
        <section className="space-y-3">
          <h2 className="text-lg font-medium text-slate-800">Logs &amp; observability</h2>
          <LogsPanel />
        </section>
      )}
    </div>
  );
}

export default App;
