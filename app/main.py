import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_IN_PROGRESS,
    HTTP_REQUESTS_TOTAL,
)
from app.db.redis import redis_client
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
        await redis_client.aclose()
        await engine.dispose()
        logger.info("Stopping %s", settings.name)


app = FastAPI(
    title=settings.name,
    version=settings.version,
    debug=settings.debug,
    lifespan=lifespan,
)


@app.middleware("http")
async def collect_http_metrics(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    HTTP_REQUESTS_IN_PROGRESS.inc()

    started_at = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code

        return response

    finally:
        duration = time.perf_counter() - started_at

        route = request.scope.get("route")
        route_path = getattr(route, "path", "unmatched")

        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            route=route_path,
            status_code=str(status_code),
        ).inc()

        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            route=route_path,
        ).observe(duration)

        HTTP_REQUESTS_IN_PROGRESS.dec()


@app.get("/metrics", include_in_schema=False)
async def prometheus_metrics() -> Response:
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


app.include_router(api_router)
