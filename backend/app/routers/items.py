from fastapi import APIRouter

from app.schemas.items import ItemListResponse
from app.services.ingestion import list_items

router = APIRouter(tags=["items"])


@router.get("/items", response_model=ItemListResponse)
async def get_items() -> ItemListResponse:
    return ItemListResponse(items=list_items())
