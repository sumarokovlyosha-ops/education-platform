from fastapi import FastAPI

from app.api.routers.health import router as health_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.name,
    version=settings.version,
    debug=settings.debug
)

app.include_router(health_router)