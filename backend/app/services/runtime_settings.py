"""Operational knobs an operator can tune without redeploying: which
provider to use, chunk size/overlap, and how many chunks to retrieve.
Stored in SQLite (single row) rather than env so they're editable at
runtime via PUT /settings. Secrets never live here -- see app/core/config.py.
"""

import logging

from app.core.errors import InvalidInputError
from app.db.connection import get_connection
from app.schemas.settings import RuntimeSettingsResponse, RuntimeSettingsUpdateRequest

logger = logging.getLogger(__name__)

_VALID_EMBEDDING_PROVIDERS = {"gemini", "local"}
_VALID_GENERATION_PROVIDERS = {"gemini", "groq", "local"}


def get_runtime_settings() -> RuntimeSettingsResponse:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM runtime_settings WHERE id = 1").fetchone()
    return RuntimeSettingsResponse(**dict(row))


def update_runtime_settings(patch: RuntimeSettingsUpdateRequest) -> RuntimeSettingsResponse:
    current = get_runtime_settings()
    merged = current.model_copy(update=patch.model_dump(exclude_none=True))

    if merged.embedding_provider not in _VALID_EMBEDDING_PROVIDERS:
        raise InvalidInputError(
            f"embedding_provider must be one of {sorted(_VALID_EMBEDDING_PROVIDERS)}"
        )
    if merged.generation_provider not in _VALID_GENERATION_PROVIDERS:
        raise InvalidInputError(
            f"generation_provider must be one of {sorted(_VALID_GENERATION_PROVIDERS)}"
        )
    if merged.chunk_overlap_chars >= merged.chunk_size_chars:
        raise InvalidInputError("chunk_overlap_chars must be smaller than chunk_size_chars")

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE runtime_settings
            SET embedding_provider = ?, generation_provider = ?,
                chunk_size_chars = ?, chunk_overlap_chars = ?, top_k = ?
            WHERE id = 1
            """,
            (
                merged.embedding_provider,
                merged.generation_provider,
                merged.chunk_size_chars,
                merged.chunk_overlap_chars,
                merged.top_k,
            ),
        )

    logger.info("settings.updated %s", merged.model_dump())
    return merged
