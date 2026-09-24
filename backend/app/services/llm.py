"""Generation provider abstraction. Swappable via GENERATION_PROVIDER."""

import logging
from abc import ABC, abstractmethod
from functools import lru_cache

import httpx

from app.core.config import get_settings
from app.core.errors import ProviderError

logger = logging.getLogger(__name__)


class GenerationProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Return the model's answer text for a fully-built prompt."""


class GeminiGeneration(GenerationProvider):
    def __init__(self, api_key: str):
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel("gemini-3.5-flash-lite")

    def generate(self, prompt: str) -> str:
        try:
            response = self._model.generate_content(prompt)
            return response.text
        except Exception as exc:
            logger.warning("generation.gemini_call_failed error=%s", exc)
            raise ProviderError(f"Gemini generation call failed: {exc}") from exc


class GroqGeneration(GenerationProvider):
    def __init__(self, api_key: str):
        try:
            from groq import Groq
        except ImportError as exc:
            raise ProviderError(
                "GENERATION_PROVIDER=groq requires the groq package. Run: pip install groq"
            ) from exc

        self._client = Groq(api_key=api_key)

    def generate(self, prompt: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except Exception as exc:
            logger.warning("generation.groq_call_failed error=%s", exc)
            raise ProviderError(f"Groq generation call failed: {exc}") from exc


class LocalGeneration(GenerationProvider):
    def __init__(self, base_url: str, model: str):
        self._base_url = base_url.rstrip("/")
        self._model = model

    def generate(self, prompt: str) -> str:
        try:
            resp = httpx.post(
                f"{self._base_url}/api/generate",
                json={"model": self._model, "prompt": prompt, "stream": False},
                timeout=60.0,
            )
            resp.raise_for_status()
            return resp.json()["response"]
        except Exception as exc:
            logger.warning("generation.local_call_failed error=%s", exc)
            raise ProviderError(f"Local (Ollama) generation call failed: {exc}") from exc


@lru_cache
def get_generation_provider(provider_name: str) -> GenerationProvider:
    settings = get_settings()
    if provider_name == "gemini":
        if not settings.gemini_api_key:
            raise ProviderError("GENERATION_PROVIDER=gemini requires GEMINI_API_KEY")
        return GeminiGeneration(settings.gemini_api_key)
    if provider_name == "groq":
        if not settings.groq_api_key:
            raise ProviderError("GENERATION_PROVIDER=groq requires GROQ_API_KEY")
        return GroqGeneration(settings.groq_api_key)
    if provider_name == "local":
        return LocalGeneration(settings.ollama_base_url, settings.ollama_generation_model)
    raise ProviderError(f"Unknown generation provider: {provider_name}")
