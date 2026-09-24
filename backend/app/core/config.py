from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    embedding_provider: str = "gemini"  # gemini | local
    generation_provider: str = "gemini"  # gemini | groq | local

    gemini_api_key: str | None = None
    groq_api_key: str | None = None

    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_generation_model: str = "llama3.1:8b"

    database_path: str = "./knowledge_inbox.db"

    chunk_size_chars: int = 800
    chunk_overlap_chars: int = 100

    top_k: int = 4

    allowed_origins: str = "http://localhost:5173"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
