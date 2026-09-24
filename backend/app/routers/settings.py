from fastapi import APIRouter

from app.schemas.settings import RuntimeSettingsResponse, RuntimeSettingsUpdateRequest
from app.services.runtime_settings import get_runtime_settings, update_runtime_settings

router = APIRouter(tags=["settings"])


@router.get("/settings", response_model=RuntimeSettingsResponse)
async def read_settings() -> RuntimeSettingsResponse:
    return get_runtime_settings()


@router.put("/settings", response_model=RuntimeSettingsResponse)
async def write_settings(request: RuntimeSettingsUpdateRequest) -> RuntimeSettingsResponse:
    return update_runtime_settings(request)
