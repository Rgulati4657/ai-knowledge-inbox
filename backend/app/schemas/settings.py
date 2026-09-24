from pydantic import BaseModel, Field


class RuntimeSettingsResponse(BaseModel):
    embedding_provider: str
    generation_provider: str
    chunk_size_chars: int
    chunk_overlap_chars: int
    top_k: int


class RuntimeSettingsUpdateRequest(BaseModel):
    """All fields optional: PATCH-style partial update.

    Secrets (API keys) are never part of this model -- they only ever come
    from the server's own .env and are not readable or writable over HTTP.
    """

    embedding_provider: str | None = None
    generation_provider: str | None = None
    chunk_size_chars: int | None = Field(None, gt=0)
    chunk_overlap_chars: int | None = Field(None, ge=0)
    top_k: int | None = Field(None, ge=1, le=20)
