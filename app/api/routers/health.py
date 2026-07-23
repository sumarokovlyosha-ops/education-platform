from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(prefix="/health",tags=["Health"])


@router.get("/live",response_model=HealthResponse)
async def liveness() -> HealthResponse:
    return HealthResponse(status="ok")