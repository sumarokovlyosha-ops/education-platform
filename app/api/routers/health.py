import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.health import HealthResponse


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)

logger = logging.getLogger(__name__)

SessionDependency = Annotated[
    AsyncSession,
    Depends(get_session),
]


@router.get(
    "/live",
    response_model=HealthResponse,
)
async def liveness() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    response_model=HealthResponse,
)
async def readiness(
    session: SessionDependency,
) -> HealthResponse:
    try:
        result = await session.execute(text("SELECT 1"))
        result.scalar_one()
    except SQLAlchemyError:
        logger.exception("Database readiness check failed")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from None

    return HealthResponse(status="ok")
