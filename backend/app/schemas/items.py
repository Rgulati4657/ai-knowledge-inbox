from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class SourceType(str, Enum):
    note = "note"
    url = "url"


class IngestRequest(BaseModel):
    source_type: SourceType
    content: str = Field(..., min_length=1, max_length=20_000)

    @field_validator("content")
    @classmethod
    def strip_and_check(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("content must not be blank")
        return stripped


class ItemResponse(BaseModel):
    id: int
    source_type: SourceType
    source_url: str | None
    content_preview: str
    chunk_count: int
    created_at: datetime


class IngestResponse(BaseModel):
    item: ItemResponse


class ItemListResponse(BaseModel):
    items: list[ItemResponse]


class BulkIngestRequest(BaseModel):
    items: list[IngestRequest] = Field(..., min_length=1, max_length=50)


class BulkIngestResult(BaseModel):
    source_type: SourceType
    content: str
    item: ItemResponse | None
    error: str | None


class BulkIngestResponse(BaseModel):
    results: list[BulkIngestResult]
