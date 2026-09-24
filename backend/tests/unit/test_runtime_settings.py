import pytest

from app.core.errors import InvalidInputError
from app.schemas.settings import RuntimeSettingsUpdateRequest
from app.services.runtime_settings import get_runtime_settings, update_runtime_settings


def test_get_runtime_settings_returns_env_seeded_defaults(temp_db):
    settings = get_runtime_settings()
    assert settings.embedding_provider == "gemini"
    assert settings.chunk_size_chars == 800
    assert settings.chunk_overlap_chars == 100
    assert settings.top_k == 4


def test_update_runtime_settings_persists_partial_change(temp_db):
    updated = update_runtime_settings(RuntimeSettingsUpdateRequest(top_k=8))
    assert updated.top_k == 8
    assert updated.chunk_size_chars == 800  # untouched fields preserved

    reloaded = get_runtime_settings()
    assert reloaded.top_k == 8


def test_update_rejects_unknown_embedding_provider(temp_db):
    with pytest.raises(InvalidInputError):
        update_runtime_settings(RuntimeSettingsUpdateRequest(embedding_provider="openai"))


def test_update_rejects_overlap_not_smaller_than_chunk_size(temp_db):
    with pytest.raises(InvalidInputError):
        update_runtime_settings(
            RuntimeSettingsUpdateRequest(chunk_size_chars=100, chunk_overlap_chars=100)
        )
