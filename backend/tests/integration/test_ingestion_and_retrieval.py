import pytest

from app.core.errors import InvalidInputError
from app.schemas.items import IngestRequest, SourceType
from app.services.ingestion import fetch_url_text, ingest_item, list_items
from app.services.retrieval import retrieve_top_k
from tests.conftest import FakeEmbeddingProvider

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def _ingest(provider, source_type, content):
    return ingest_item(provider, CHUNK_SIZE, CHUNK_OVERLAP, IngestRequest(source_type=source_type, content=content))


def test_ingest_note_creates_item_and_chunks(temp_db):
    provider = FakeEmbeddingProvider()

    item = _ingest(provider, SourceType.note, "hello world " * 100)

    assert item.id == 1
    assert item.source_type == SourceType.note
    assert item.source_url is None
    assert item.chunk_count > 1


def test_list_items_returns_all_ingested(temp_db):
    provider = FakeEmbeddingProvider()

    _ingest(provider, SourceType.note, "first note content")
    _ingest(provider, SourceType.note, "second note content")

    items = list_items()
    assert len(items) == 2
    assert {i.content_preview for i in items} == {"first note content", "second note content"}


def test_fetch_url_text_rejects_non_http_scheme():
    with pytest.raises(InvalidInputError):
        fetch_url_text("ftp://example.com/file")


def test_retrieve_top_k_ranks_matching_item_first(temp_db):
    provider = FakeEmbeddingProvider()

    _ingest(provider, SourceType.note, "bananas are yellow fruit")
    _ingest(provider, SourceType.note, "rockets launch into orbit")

    query_vector = provider.embed_query("tell me about bananas and fruit")
    results = retrieve_top_k(query_vector, top_k=2)

    assert len(results) == 2
    assert "banana" in results[0].snippet.lower()


def test_retrieve_top_k_returns_empty_when_no_items(temp_db):
    provider = FakeEmbeddingProvider()
    results = retrieve_top_k(provider.embed_query("anything"), top_k=4)
    assert results == []
