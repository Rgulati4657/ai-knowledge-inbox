import pytest

from app.services.chunking import chunk_text


def test_empty_text_returns_no_chunks():
    assert chunk_text("", chunk_size_chars=100, overlap_chars=10) == []
    assert chunk_text("   ", chunk_size_chars=100, overlap_chars=10) == []


def test_short_text_returns_single_chunk():
    text = "hello world this is short"
    chunks = chunk_text(text, chunk_size_chars=100, overlap_chars=10)
    assert chunks == [text]


def test_long_text_splits_into_multiple_chunks_without_breaking_words():
    text = " ".join(f"word{i}" for i in range(200))
    chunks = chunk_text(text, chunk_size_chars=50, overlap_chars=10)
    assert len(chunks) > 1
    for chunk in chunks:
        for token in chunk.split():
            assert token in text.split()


def test_consecutive_chunks_share_overlap():
    text = " ".join(f"word{i}" for i in range(50))
    chunks = chunk_text(text, chunk_size_chars=100, overlap_chars=30)
    assert set(chunks[0].split()) & set(chunks[1].split())


def test_rejects_invalid_sizes():
    with pytest.raises(ValueError):
        chunk_text("text", chunk_size_chars=0, overlap_chars=0)
    with pytest.raises(ValueError):
        chunk_text("text", chunk_size_chars=10, overlap_chars=10)
    with pytest.raises(ValueError):
        chunk_text("text", chunk_size_chars=10, overlap_chars=-1)
