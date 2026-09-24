from fastapi import APIRouter, Depends

from app.core.dependencies import (
    current_embedding_provider,
    current_generation_provider,
    current_runtime_settings,
)
from app.schemas.query import QueryRequest, QueryResponse
from app.schemas.settings import RuntimeSettingsResponse
from app.services.embeddings import EmbeddingProvider
from app.services.llm import GenerationProvider
from app.services.rag import answer_question

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    embedding_provider: EmbeddingProvider = Depends(current_embedding_provider),
    generation_provider: GenerationProvider = Depends(current_generation_provider),
    settings: RuntimeSettingsResponse = Depends(current_runtime_settings),
) -> QueryResponse:
    return answer_question(request.question, settings.top_k, embedding_provider, generation_provider)
