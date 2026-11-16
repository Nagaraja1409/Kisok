from __future__ import annotations

from fastapi import APIRouter
from app.core.config import get_core_settings
from app.providers.router import ProviderRouter
from app.schemas.v1 import HealthV1Response

router = APIRouter(prefix="/api/v1", tags=["Health"])


@router.get("/health", response_model=HealthV1Response)
async def health_v1() -> HealthV1Response:
    """Check AI platform health, active LLM providers, and ERP mode."""
    settings = get_core_settings()
    router_svc = ProviderRouter(settings)
    providers_health = await router_svc.get_health_status()

    return HealthV1Response(
        status="ok",
        version="1.0.0",
        app_name=settings.app_name,
        erp_mode=settings.erp_mode,
        ai_provider=settings.ai_provider,
        providers_health=providers_health,
    )
