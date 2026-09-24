from fastapi import APIRouter, Query

from app.core.logging_config import get_recent_logs
from app.schemas.logs import LogEntry, LogListResponse

router = APIRouter(tags=["logs"])


@router.get("/logs", response_model=LogListResponse)
async def read_logs(
    limit: int = Query(100, ge=1, le=500),
    level: str | None = None,
) -> LogListResponse:
    entries = get_recent_logs(limit=limit, level=level)
    return LogListResponse(logs=[LogEntry(**entry) for entry in entries])
