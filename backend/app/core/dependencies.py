"""FastAPI dependency providers. Routers ask for these instead of reaching
into a global app.state, which keeps route handlers testable: tests can
override any of these with fakes via app.dependency_overrides.
"""

from fastapi import Depends

from app.schemas.settings import RuntimeSettingsResponse
from app.services.embeddings import EmbeddingProvider, get_embedding_provider
from app.services.llm import GenerationProvider, get_generation_provider
from app.services.runtime_settings import get_runtime_settings


def current_runtime_settings() -> RuntimeSettingsResponse:
    return get_runtime_settings()


def current_embedding_provider(
    settings: RuntimeSettingsResponse = Depends(current_runtime_settings),
) -> EmbeddingProvider:
    return get_embedding_provider(settings.embedding_provider)


def current_generation_provider(
    settings: RuntimeSettingsResponse = Depends(current_runtime_settings),
) -> GenerationProvider:
    return get_generation_provider(settings.generation_provider)
