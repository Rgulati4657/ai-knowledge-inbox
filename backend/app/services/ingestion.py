import logging
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.errors import FetchError, InvalidInputError
from app.db.connection import get_connection, serialize_embedding
from app.schemas.items import IngestRequest, ItemResponse, SourceType
from app.services.chunking import chunk_text
from app.services.embeddings import EmbeddingProvider

logger = logging.getLogger(__name__)

_FETCH_TIMEOUT_SECONDS = 10.0
# Hard cap on extracted text so one huge page can't blow up embedding cost/
# memory in a single request. A real crawler would page/stream instead.
_MAX_URL_CONTENT_CHARS = 100_000


def fetch_url_text(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise InvalidInputError(f"Not a valid http(s) URL: {url}")

    try:
        response = httpx.get(
            url,
            timeout=_FETCH_TIMEOUT_SECONDS,
            follow_redirects=True,
            headers={"User-Agent": "ai-knowledge-inbox/1.0"},
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("ingestion.url_fetch_failed url=%s error=%s", url, exc)
        raise FetchError(f"Could not fetch {url}: {exc}") from exc

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = " ".join(soup.get_text(separator=" ").split())
    if not text:
        raise FetchError(f"No extractable text content at {url}")

    if len(text) > _MAX_URL_CONTENT_CHARS:
        logger.warning(
            "ingestion.url_content_truncated url=%s original_chars=%s cap=%s",
            url,
            len(text),
            _MAX_URL_CONTENT_CHARS,
        )
        text = text[:_MAX_URL_CONTENT_CHARS]

    return text


def ingest_item(
    embedding_provider: EmbeddingProvider,
    chunk_size_chars: int,
    chunk_overlap_chars: int,
    request: IngestRequest,
) -> ItemResponse:
    if request.source_type == SourceType.url:
        source_url = request.content
        raw_content = fetch_url_text(request.content)
    else:
        source_url = None
        raw_content = request.content

    chunks = chunk_text(raw_content, chunk_size_chars, chunk_overlap_chars)
    if not chunks:
        raise InvalidInputError("Content produced no chunks after cleaning")

    embeddings = embedding_provider.embed_documents(chunks)

    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO items (source_type, source_url, raw_content) VALUES (?, ?, ?)",
            (request.source_type.value, source_url, raw_content),
        )
        item_id = cursor.lastrowid

        conn.executemany(
            "INSERT INTO chunks (item_id, chunk_index, chunk_text, embedding) VALUES (?, ?, ?, ?)",
            [
                (item_id, index, chunk, serialize_embedding(vector))
                for index, (chunk, vector) in enumerate(zip(chunks, embeddings))
            ],
        )

        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()

    logger.info(
        "ingestion.item_created item_id=%s source_type=%s chunk_count=%s",
        item_id,
        request.source_type.value,
        len(chunks),
    )

    return ItemResponse(
        id=row["id"],
        source_type=row["source_type"],
        source_url=row["source_url"],
        content_preview=row["raw_content"][:200],
        chunk_count=len(chunks),
        created_at=row["created_at"],
    )


def list_items() -> list[ItemResponse]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT items.*, COUNT(chunks.id) AS chunk_count
            FROM items
            LEFT JOIN chunks ON chunks.item_id = items.id
            GROUP BY items.id
            ORDER BY items.created_at DESC
            """
        ).fetchall()

    return [
        ItemResponse(
            id=row["id"],
            source_type=row["source_type"],
            source_url=row["source_url"],
            content_preview=row["raw_content"][:200],
            chunk_count=row["chunk_count"],
            created_at=row["created_at"],
        )
        for row in rows
    ]
