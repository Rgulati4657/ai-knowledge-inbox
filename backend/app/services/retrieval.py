"""Brute-force cosine similarity search over every chunk in SQLite.

Fine at hundreds-to-low-thousands of chunks (a numpy matmul over the whole
table, still sub-100ms). Does NOT scale past that -- see docs/ARCHITECTURE.md
"What breaks at scale" for the pgvector/FAISS migration path.
"""

import logging

import numpy as np

from app.db.connection import deserialize_embedding, get_connection
from app.schemas.query import SourceSnippet
from app.schemas.items import SourceType

logger = logging.getLogger(__name__)


def retrieve_top_k(query_vector: list[float], top_k: int) -> list[SourceSnippet]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT chunks.item_id, chunks.chunk_text, chunks.embedding,
                   items.source_type, items.source_url
            FROM chunks
            JOIN items ON items.id = chunks.item_id
            """
        ).fetchall()

    if not rows:
        return []

    matrix = np.array([deserialize_embedding(row["embedding"]) for row in rows])
    query = np.array(query_vector)

    matrix_norms = np.linalg.norm(matrix, axis=1)
    query_norm = np.linalg.norm(query)
    similarities = (matrix @ query) / (matrix_norms * query_norm + 1e-10)

    top_indices = np.argsort(similarities)[::-1][:top_k]

    logger.info("retrieval.query total_chunks=%s top_k=%s", len(rows), top_k)

    return [
        SourceSnippet(
            item_id=rows[i]["item_id"],
            source_type=SourceType(rows[i]["source_type"]),
            source_url=rows[i]["source_url"],
            snippet=rows[i]["chunk_text"],
            similarity=float(similarities[i]),
        )
        for i in top_indices
    ]
