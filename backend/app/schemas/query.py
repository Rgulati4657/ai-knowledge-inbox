from pydantic import BaseModel, Field, field_validator

from app.schemas.items import SourceType


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2_000)

    @field_validator("question")
    @classmethod
    def strip_and_check(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("question must not be blank")
        return stripped


class SourceSnippet(BaseModel):
    item_id: int
    source_type: SourceType
    source_url: str | None
    snippet: str
    similarity: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceSnippet]
