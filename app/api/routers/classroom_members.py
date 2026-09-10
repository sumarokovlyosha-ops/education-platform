from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.classroom_member import ClassroomMemberCreate, ClassroomMemberRead
from app.services.classroom_member import (
    ClassroomMemberAlreadyExistsError,
    ClassroomMemberInactiveClassroomError,
    ClassroomMemberInactiveMembershipError,
    ClassroomMemberNotFoundError,
    ClassroomMemberRoleRequiredError,
    ClassroomMemberSchoolMismatchError,
    ClassroomMemberService,
    MemberClassroomNotFoundError,
    MemberMembershipNotFoundError,
)

router = APIRouter(
    prefix="/classes/{classroom_id}/members",
    tags=["Classroom members"],
)


@router.post(
    "",
    response_model=ClassroomMemberRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_classroom_member(
    classroom_id: UUID,
    data: ClassroomMemberCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ClassroomMemberRead:
    member_service = ClassroomMemberService(session=session)

    try:
        orm_member = await member_service.add_member(
            classroom_id=classroom_id,
            data=data,
        )
    except MemberClassroomNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found",
        ) from error
    except MemberMembershipNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found",
        ) from error
    except ClassroomMemberSchoolMismatchError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Classroom and membership belong to different schools",
        ) from error
    except ClassroomMemberInactiveClassroomError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Classroom is inactive",
        ) from error
    except ClassroomMemberInactiveMembershipError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Membership is inactive",
        ) from error
    except ClassroomMemberRoleRequiredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Membership does not have the required school role",
        ) from error
    except ClassroomMemberAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Classroom member already exists",
        ) from error

    return ClassroomMemberRead.model_validate(orm_member)


@router.get(
    "",
    response_model=list[ClassroomMemberRead],
    status_code=status.HTTP_200_OK,
)
async def get_classroom_members(
    classroom_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ClassroomMemberRead]:
    member_service = ClassroomMemberService(session=session)

    try:
        orm_members = await member_service.list_members(
            classroom_id=classroom_id,
            limit=limit,
            offset=offset,
        )
    except MemberClassroomNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found",
        ) from error

    return [ClassroomMemberRead.model_validate(member) for member in orm_members]


@router.delete(
    "/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_classroom_member(
    classroom_id: UUID,
    membership_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    member_service = ClassroomMemberService(session=session)

    try:
        await member_service.remove_member(
            classroom_id=classroom_id,
            membership_id=membership_id,
        )
    except ClassroomMemberNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom member not found",
        ) from error
