"""Embedding provider abstraction.

Swappable via EMBEDDING_PROVIDER so the rest of the pipeline never imports
a specific SDK. Only gemini and local are implemented — Groq has no
embeddings endpoint, which is exactly why generation and embedding
providers are configured independently rather than one shared PROVIDER
flag. See docs/ARCHITECTURE.md.
"""

import logging
from abc import ABC, abstractmethod
from functools import lru_cache

from app.core.config import get_settings
from app.core.errors import ProviderError

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed content being stored for later retrieval. One vector per text, same order."""

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Embed a search query. Kept separate from embed_documents because
        some providers (Gemini) use an asymmetric model where a query and a
        document are embedded differently on purpose, so a well-phrased
        question's vector lands close to the matching document's vector
        rather than requiring identical text to match.
        """


class GeminiEmbeddings(EmbeddingProvider):
    def __init__(self, api_key: str):
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self._genai = genai

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed_many(texts, task_type="retrieval_document")

    def embed_query(self, text: str) -> list[float]:
        return self._embed_many([text], task_type="retrieval_query")[0]

    def _embed_many(self, texts: list[str], task_type: str) -> list[list[float]]:
        try:
            vectors = []
            for text in texts:
                result = self._genai.embed_content(
                    model="models/gemini-embedding-001",
                    content=text,
                    task_type=task_type,
                )
                vectors.append(result["embedding"])
            return vectors
        except Exception as exc:
            logger.warning("embeddings.gemini_call_failed error=%s", exc)
            raise ProviderError(f"Gemini embedding call failed: {exc}") from exc


class LocalEmbeddings(EmbeddingProvider):
    """sentence-transformers running on-device. No API key, slower cold start.

    all-MiniLM-L6-v2 is a symmetric model (query and document share the same
    embedding space by construction), so embed_query is just embed_documents
    for a single text -- there is no separate query mode to ask for.
    """

    _MODEL_NAME = "all-MiniLM-L6-v2"

    def __init__(self):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ProviderError(
                "EMBEDDING_PROVIDER=local requires sentence-transformers, which is not "
                "installed by default (see requirements.txt). Run: "
                "pip install sentence-transformers"
            ) from exc

        self._model = SentenceTransformer(self._MODEL_NAME)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        try:
            return self._model.encode(texts, convert_to_numpy=True).tolist()
        except Exception as exc:
            logger.warning("embeddings.local_call_failed error=%s", exc)
            raise ProviderError(f"Local embedding call failed: {exc}") from exc

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


@lru_cache
def get_embedding_provider(provider_name: str) -> EmbeddingProvider:
    """Cached per provider name -- LocalEmbeddings loads a model on
    construction, so switching providers back and forth at runtime (via
    PUT /settings) doesn't reload it every time.
    """
    settings = get_settings()
    if provider_name == "gemini":
        if not settings.gemini_api_key:
            raise ProviderError("EMBEDDING_PROVIDER=gemini requires GEMINI_API_KEY")
        return GeminiEmbeddings(settings.gemini_api_key)
    if provider_name == "local":
        return LocalEmbeddings()
    raise ProviderError(f"Unknown embedding provider: {provider_name}")
