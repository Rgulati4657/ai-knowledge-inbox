from app.schemas.items import IngestRequest, SourceType
from app.services.ingestion import ingest_item
from app.services.rag import answer_question
from tests.conftest import FakeEmbeddingProvider, FakeGenerationProvider


def test_answer_question_with_no_items_returns_fallback(temp_db):
    result = answer_question("anything?", 4, FakeEmbeddingProvider(), FakeGenerationProvider())
    assert result.sources == []
    assert "No content has been ingested" in result.answer


def test_answer_question_with_items_returns_answer_and_sources(temp_db):
    embedder = FakeEmbeddingProvider()
    ingest_item(embedder, 800, 100, IngestRequest(source_type=SourceType.note, content="the sky is blue"))

    result = answer_question("what color is the sky?", 4, embedder, FakeGenerationProvider())

    assert result.answer.startswith("FAKE_ANSWER")
    assert len(result.sources) == 1
    assert "sky" in result.sources[0].snippet.lower()
