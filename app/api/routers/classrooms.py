from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.classroom import ClassroomCache
from app.db.redis import get_redis
from app.db.session import get_session
from app.schemas.classroom import ClassroomCreate, ClassroomRead
from app.services.classroom import (
    ClassroomAlreadyExistsError,
    ClassroomNotFoundError,
    ClassroomSchoolNotFoundError,
    ClassroomService,
)

router = APIRouter(tags=["Classrooms"])


@router.post(
    "/schools/{school_id}/classes",
    response_model=ClassroomRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_classroom(
    school_id: UUID,
    data: ClassroomCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> ClassroomRead:
    classroom_service = ClassroomService(
        session=session,
        cache=ClassroomCache(redis),
    )

    try:
        orm_classroom = await classroom_service.create_classroom(
            school_id=school_id,
            data=data,
        )
    except ClassroomSchoolNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        ) from error
    except ClassroomAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Classroom already exists",
        ) from error

    return ClassroomRead.model_validate(orm_classroom)


@router.get(
    "/schools/{school_id}/classes",
    response_model=list[ClassroomRead],
    status_code=status.HTTP_200_OK,
)
async def get_school_classrooms(
    school_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    redis: Annotated[Redis, Depends(get_redis)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ClassroomRead]:
    classroom_service = ClassroomService(
        session=session,
        cache=ClassroomCache(redis),
    )

    try:
        classrooms = await classroom_service.list_school_classrooms(
            school_id=school_id,
            limit=limit,
            offset=offset,
        )
    except ClassroomSchoolNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        ) from error

    return classrooms


@router.get(
    "/classes/{classroom_id}",
    response_model=ClassroomRead,
    status_code=status.HTTP_200_OK,
)
async def get_classroom(
    classroom_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> ClassroomRead:
    classroom_service = ClassroomService(
        session=session,
        cache=ClassroomCache(redis),
    )

    try:
        orm_classroom = await classroom_service.get_classroom(
            classroom_id=classroom_id,
        )
    except ClassroomNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found",
        ) from error

    return ClassroomRead.model_validate(orm_classroom)
