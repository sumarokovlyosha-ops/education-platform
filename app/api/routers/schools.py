from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.membership import MembershipCreate, MembershipRead
from app.schemas.school import SchoolCreate, SchoolRead
from app.services.membership import (
    MembershipAlreadyExistsError,
    MembershipSchoolNotFoundError,
    MembershipService,
    MembershipUserNotFoundError,
)
from app.services.school import SchoolNotFoundError, SchoolService

router = APIRouter(prefix="/schools", tags=["Schools"])


@router.post(
    "",
    response_model=SchoolRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_school(
    data: SchoolCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SchoolRead:
    school_service = SchoolService(session=session)

    orm_school = await school_service.create_school(data=data)

    return SchoolRead.model_validate(orm_school)


@router.get(
    "",
    response_model=list[SchoolRead],
    status_code=status.HTTP_200_OK,
)
async def get_schools(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[SchoolRead]:
    school_service = SchoolService(session=session)

    orm_schools = await school_service.list_schools(
        limit=limit,
        offset=offset,
    )

    return [SchoolRead.model_validate(school) for school in orm_schools]


@router.get(
    "/{school_id}",
    response_model=SchoolRead,
    status_code=status.HTTP_200_OK,
)
async def get_school(
    school_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SchoolRead:
    school_service = SchoolService(session=session)

    try:
        orm_school = await school_service.get_school(
            school_id=school_id,
        )
    except SchoolNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        ) from error

    return SchoolRead.model_validate(orm_school)


@router.post(
    "/{school_id}/memberships",
    response_model=MembershipRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_membership(
    school_id: UUID,
    data: MembershipCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MembershipRead:
    membership_service = MembershipService(session=session)

    try:
        orm_membership = await membership_service.create_membership(
            user_id=data.user_id,
            school_id=school_id,
        )

    except MembershipUserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        ) from error

    except MembershipSchoolNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        ) from error

    except MembershipAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Membership already exists",
        ) from error

    return MembershipRead.model_validate(orm_membership)


@router.get(
    "/{school_id}/memberships",
    response_model=list[MembershipRead],
    status_code=status.HTTP_200_OK,
)
async def get_school_memberships(
    school_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[MembershipRead]:
    membership_service = MembershipService(session=session)

    try:
        orm_memberships = await membership_service.list_school_memberships(
            school_id=school_id,
        )

    except MembershipSchoolNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found",
        ) from error

    return [MembershipRead.model_validate(membership) for membership in orm_memberships]
