import logging

from fastapi import APIRouter, Depends

from app.core.dependencies import current_embedding_provider, current_runtime_settings
from app.schemas.items import (
    BulkIngestRequest,
    BulkIngestResponse,
    BulkIngestResult,
    IngestRequest,
    IngestResponse,
)
from app.schemas.settings import RuntimeSettingsResponse
from app.services.embeddings import EmbeddingProvider
from app.services.ingestion import ingest_item

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse, status_code=201)
async def ingest(
    request: IngestRequest,
    embedding_provider: EmbeddingProvider = Depends(current_embedding_provider),
    settings: RuntimeSettingsResponse = Depends(current_runtime_settings),
) -> IngestResponse:
    item = ingest_item(
        embedding_provider, settings.chunk_size_chars, settings.chunk_overlap_chars, request
    )
    return IngestResponse(item=item)


@router.post("/ingest/bulk", response_model=BulkIngestResponse)
async def ingest_bulk(
    request: BulkIngestRequest,
    embedding_provider: EmbeddingProvider = Depends(current_embedding_provider),
    settings: RuntimeSettingsResponse = Depends(current_runtime_settings),
) -> BulkIngestResponse:
    """Sequential, in-process -- no worker pool or queue. Fine for a batch
    of a few dozen documents; one slow/failing item can't corrupt the rest
    since each is wrapped independently. See docs/ARCHITECTURE.md for the
    background-job upgrade path once volume makes this block too long.
    """
    results = []
    for item_request in request.items:
        try:
            item = ingest_item(
                embedding_provider,
                settings.chunk_size_chars,
                settings.chunk_overlap_chars,
                item_request,
            )
            results.append(
                BulkIngestResult(
                    source_type=item_request.source_type,
                    content=item_request.content,
                    item=item,
                    error=None,
                )
            )
        except Exception as exc:
            logger.warning(
                "ingestion.bulk_item_failed content=%r error=%s", item_request.content[:80], exc
            )
            results.append(
                BulkIngestResult(
                    source_type=item_request.source_type,
                    content=item_request.content,
                    item=None,
                    error=str(exc),
                )
            )
    return BulkIngestResponse(results=results)
