import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from app.core.config import get_settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL CHECK (source_type IN ('note', 'url')),
    source_url TEXT,
    raw_content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chunks_item_id ON chunks(item_id);

-- Single-row table: operational knobs editable at runtime via /settings,
-- as opposed to secrets/infra config which only ever live in .env.
CREATE TABLE IF NOT EXISTS runtime_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    embedding_provider TEXT NOT NULL,
    generation_provider TEXT NOT NULL,
    chunk_size_chars INTEGER NOT NULL,
    chunk_overlap_chars INTEGER NOT NULL,
    top_k INTEGER NOT NULL
);
"""


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    conn = sqlite3.connect(settings.database_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(_SCHEMA)
        _seed_runtime_settings(conn)


def _seed_runtime_settings(conn: sqlite3.Connection) -> None:
    """First boot only: copy the env-configured defaults into the
    runtime_settings row so /settings has something to read immediately.
    """
    exists = conn.execute("SELECT 1 FROM runtime_settings WHERE id = 1").fetchone()
    if exists:
        return

    settings = get_settings()
    conn.execute(
        """
        INSERT INTO runtime_settings
            (id, embedding_provider, generation_provider, chunk_size_chars, chunk_overlap_chars, top_k)
        VALUES (1, ?, ?, ?, ?, ?)
        """,
        (
            settings.embedding_provider,
            settings.generation_provider,
            settings.chunk_size_chars,
            settings.chunk_overlap_chars,
            settings.top_k,
        ),
    )


def serialize_embedding(vector: list[float]) -> str:
    return json.dumps(vector)


def deserialize_embedding(raw: str) -> list[float]:
    return json.loads(raw)
