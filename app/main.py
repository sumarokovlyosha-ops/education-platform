import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers.health import router as health_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import engine


settings = get_settings()

configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(
    _app: FastAPI,
) -> AsyncIterator[None]:
    logger.info("Starting %s", settings.name)

    try:
        yield
    finally:
        await engine.dispose()
        logger.info("Stopping %s", settings.name)


app = FastAPI(
    title=settings.name,
    version=settings.version,
    debug=settings.debug,
    lifespan=lifespan,
)

app.include_router(health_router)
