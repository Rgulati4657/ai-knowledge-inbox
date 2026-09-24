# AI Knowledge Inbox

Save notes/URLs, ask questions over them, get answers with cited sources via a small
RAG pipeline. Built for the Turium AI take-home assignment.

Design decisions and tradeoffs: see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
Diagrams (flow chart, DFD, assignment architecture, production-grade architecture):
[docs/diagrams/architecture.drawio](docs/diagrams/architecture.drawio) - open at
[app.diagrams.net](https://app.diagrams.net) (File > Open From > Device) or with the
draw.io VS Code extension.

## Stack

- Backend: FastAPI + SQLite, pluggable embedding/generation providers (Gemini, Groq, local/Ollama)
- Frontend: React + Vite + TypeScript + Tailwind

## Prerequisites

- Python 3.11+
- Node 18+
- A free [Gemini API key](https://aistudio.google.com/apikey) (default provider), and/or
  a free [Groq API key](https://console.groq.com/keys) if you want Groq for generation.

## Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: set GEMINI_API_KEY (and/or GROQ_API_KEY)

uvicorn app.main:app --reload --port 8000
```

Runs on http://localhost:8000. Interactive API docs at http://localhost:8000/docs.

Run tests:

```bash
cd backend
.venv/bin/python -m pytest -q
```

### Switching providers and tuning chunking/retrieval

`EMBEDDING_PROVIDER`/`GENERATION_PROVIDER` in `backend/.env` only seed the *initial*
values on first boot. After that, providers, chunk size/overlap, and `top_k` are stored
in SQLite and editable live - either via the frontend's **Settings** tab, or directly:

```bash
curl http://localhost:8000/settings
curl -X PUT http://localhost:8000/settings -H 'Content-Type: application/json' \
  -d '{"top_k": 6, "chunk_size_chars": 500}'
```

API keys themselves (`GEMINI_API_KEY`, `GROQ_API_KEY`) always stay in `.env` only - they
are never readable or writable over HTTP.

- `local` uses `sentence-transformers` for embeddings and a local [Ollama](https://ollama.com)
  model for generation - no API key needed, but you must `pip install sentence-transformers`
  (not installed by default, it pulls in torch) and have `ollama serve` running with the
  model in `OLLAMA_GENERATION_MODEL` pulled.
- `groq` is generation-only (no Groq embeddings API) - pair it with `EMBEDDING_PROVIDER=gemini`
  or `local`.

## Frontend setup

```bash
cd frontend
npm install
cp .env.example .env   # defaults to http://localhost:8000, only change if backend port differs
npm run dev
```

Runs on http://localhost:5173.

## Running both together

Once the one-time setup above is done (`.venv` and `node_modules` exist, `.env` has a
real key), `run.py` validates the config and starts both servers for you:

```bash
python3 run.py
# or, if ports 8000/5173 are taken: python3 run.py --backend-port 8001 --frontend-port 5174
```

It checks `backend/.env` actually has the API key required for whichever provider is
configured (fails fast with the exact fix if not), confirms `backend/.venv` and
`frontend/node_modules` exist, then launches both and prints the links to open.
Ctrl+C stops both cleanly (no leftover `vite`/`uvicorn` processes).

## Using it

The frontend has three tabs:

- **Inbox** - add a note or a URL under "Add content", see it under "Saved items", then
  ask a question - the answer cites the source chunks it used.
- **Settings** - view/edit the runtime-editable provider choice, chunk size/overlap, and
  `top_k` (see "Switching providers" above). Changes to chunk size/overlap only apply to
  items ingested afterward.
- **Logs** - a live (auto-refreshing) view of the backend's structured logs: every
  request and every ingestion/retrieval/RAG step, filterable by level.

## API

| Method | Path | Body | Description |
|---|---|---|---|
| POST | `/ingest` | `{source_type: "note"\|"url", content}` | Save a note or fetch+save a URL's content |
| POST | `/ingest/bulk` | `{items: [{source_type, content}, ...]}` (max 50) | Ingest several items in one call; returns a per-item result so one failure doesn't fail the batch |
| GET | `/items` | - | List all saved items |
| POST | `/query` | `{question}` | Ask a question, get an answer + cited source chunks |
| GET | `/settings` | - | Read current runtime settings (providers, chunk size/overlap, top_k) |
| PUT | `/settings` | any subset of the fields above | Update runtime settings (validated: unknown provider or `overlap >= chunk_size` -> 400) |
| GET | `/logs?limit=&level=` | - | Recent structured log entries (in-memory, last 500) |
| GET | `/health` | - | Liveness check |

Full request/response schemas: http://localhost:8000/docs once the backend is running.

## Project structure

```
backend/app/
  main.py       # app factory, middleware, exception handlers, router wiring
  core/          # config (.env/secrets), logging (+ in-memory log capture), errors, DI
  db/            # SQLite connection + schema
  schemas/       # pydantic request/response models, one file per domain
  services/      # business logic (chunking, embeddings, llm, ingestion, retrieval, rag,
                  #  runtime_settings) - no FastAPI/HTTP imports, independently testable
  routers/       # HTTP layer only
backend/tests/
  unit/          # pure logic, no I/O (chunking, runtime settings validation, log capture)
  integration/   # hits a real temp SQLite db with fake providers
  api/           # FastAPI TestClient hitting real HTTP routes with fake providers
frontend/src/
  api/           # HTTP layer: client.ts + one file per domain + shared types.ts
  hooks/         # fetch/mutation state
  components/    # presentational
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for why it's laid out this way, the
full tradeoff writeup (chunking, vector store, provider abstraction, runtime settings,
logging), what breaks at scale, and an explicit table of edge cases covered vs. not.
