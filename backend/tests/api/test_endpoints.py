import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.dependencies import current_embedding_provider, current_generation_provider
from app.main import app
from tests.conftest import FakeEmbeddingProvider, FakeGenerationProvider


@pytest.fixture
def client(temp_db):
    app.dependency_overrides[current_embedding_provider] = lambda: FakeEmbeddingProvider()
    app.dependency_overrides[current_generation_provider] = lambda: FakeGenerationProvider()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ingest_note_then_list_items(client):
    response = client.post("/ingest", json={"source_type": "note", "content": "test note about oceans"})
    assert response.status_code == 201
    body = response.json()
    assert body["item"]["source_type"] == "note"
    assert body["item"]["chunk_count"] == 1

    listed = client.get("/items")
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1


def test_ingest_blank_note_returns_422(client):
    response = client.post("/ingest", json={"source_type": "note", "content": "   "})
    assert response.status_code == 422


def test_ingest_invalid_url_scheme_returns_400(client):
    response = client.post("/ingest", json={"source_type": "url", "content": "ftp://nope.com"})
    assert response.status_code == 400
    assert "detail" in response.json()


def test_query_with_no_items_returns_fallback_answer(client):
    response = client.post("/query", json={"question": "anything?"})
    assert response.status_code == 200
    body = response.json()
    assert body["sources"] == []
    assert "No content has been ingested" in body["answer"]


def test_query_after_ingest_returns_cited_answer(client):
    client.post("/ingest", json={"source_type": "note", "content": "the sky is blue"})
    response = client.post("/query", json={"question": "what color is the sky?"})
    assert response.status_code == 200
    body = response.json()
    assert body["answer"].startswith("FAKE_ANSWER")
    assert len(body["sources"]) == 1


def test_get_and_update_settings(client):
    current = client.get("/settings")
    assert current.status_code == 200
    assert current.json()["top_k"] == 4

    updated = client.put("/settings", json={"top_k": 7})
    assert updated.status_code == 200
    assert updated.json()["top_k"] == 7

    reread = client.get("/settings")
    assert reread.json()["top_k"] == 7


def test_update_settings_rejects_invalid_provider(client):
    response = client.put("/settings", json={"embedding_provider": "not-a-real-provider"})
    assert response.status_code == 400


def test_bulk_ingest_reports_per_item_results(client):
    response = client.post(
        "/ingest/bulk",
        json={
            "items": [
                {"source_type": "note", "content": "valid note one"},
                {"source_type": "url", "content": "ftp://invalid-scheme.com"},
            ]
        },
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 2
    assert results[0]["item"] is not None and results[0]["error"] is None
    assert results[1]["item"] is None and "Not a valid http(s) URL" in results[1]["error"]


def test_logs_endpoint_returns_recent_entries(client):
    client.get("/health")
    response = client.get("/logs?limit=10")
    assert response.status_code == 200
    assert isinstance(response.json()["logs"], list)


def test_unexpected_exception_gets_json_response_with_cors_and_is_logged(client):
    """Regression test for a real bug hit during manual testing: switching to
    a provider whose optional dependency wasn't installed raised a bare
    ModuleNotFoundError, which isn't one of our four domain exception types.
    That escaped to Starlette's default handler, which sits outside
    CORSMiddleware -- so the error response had no CORS header at all and
    the browser reported a content-free "Failed to fetch", with nothing in
    /logs to explain why. SafetyNetMiddleware in main.py exists specifically
    to catch this class of error before it reaches that point.
    """

    def _boom():
        raise RuntimeError("simulated unexpected bug, not a domain error")

    # CORS allow_origins is baked into the app at import time from .env, so
    # the test uses whatever origin is actually configured rather than a
    # hardcoded guess -- otherwise this test would be flaky against any
    # local .env that doesn't happen to list "http://localhost:5173".
    allowed_origin = get_settings().allowed_origins_list[0]

    app.dependency_overrides[current_embedding_provider] = _boom
    try:
        response = client.post(
            "/ingest",
            json={"source_type": "note", "content": "irrelevant"},
            headers={"Origin": allowed_origin},
        )
    finally:
        app.dependency_overrides[current_embedding_provider] = lambda: FakeEmbeddingProvider()

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert response.headers.get("access-control-allow-origin") == allowed_origin

    logs = client.get("/logs?limit=20").json()["logs"]
    assert any("request.unhandled_error" in entry["message"] for entry in logs)
