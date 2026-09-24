import pytest

from app.core.config import get_settings
from app.db.connection import init_db


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("DATABASE_PATH", db_path)
    get_settings.cache_clear()
    init_db()
    yield get_settings()
    get_settings.cache_clear()


class FakeEmbeddingProvider:
    """Deterministic fake: embeds text as a bag-of-words hash vector so
    similarity search behaves sensibly without any network call."""

    _DIM = 512

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_one(text)

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self._DIM
        for word in text.lower().split():
            vector[hash(word) % self._DIM] += 1.0
        return vector


class FakeGenerationProvider:
    def generate(self, prompt: str) -> str:
        return f"FAKE_ANSWER based on prompt of length {len(prompt)}"
