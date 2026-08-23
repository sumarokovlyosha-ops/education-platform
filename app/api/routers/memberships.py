from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.membership_role import MembershipRoleType
from app.schemas.membership_role import (
    MembershipRoleCreate,
    MembershipRoleRead,
)
from app.services.membership_role import (
    MembershipRoleAlreadyExistsError,
    MembershipRoleNotFoundError,
    MembershipRoleService,
    RoleMembershipNotFoundError,
)

router = APIRouter(
    prefix="/memberships",
    tags=["Memberships"],
)


@router.post(
    "/{membership_id}/roles",
    response_model=MembershipRoleRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_role(
    membership_id: UUID,
    data: MembershipRoleCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MembershipRoleRead:
    role_service = MembershipRoleService(session=session)

    try:
        orm_role = await role_service.add_role(
            membership_id=membership_id,
            role=data.role,
        )

    except RoleMembershipNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found",
        ) from error

    except MembershipRoleAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role already exists",
        ) from error

    return MembershipRoleRead.model_validate(orm_role)


@router.get(
    "/{membership_id}/roles",
    response_model=list[MembershipRoleRead],
    status_code=status.HTTP_200_OK,
)
async def get_roles(
    membership_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[MembershipRoleRead]:
    role_service = MembershipRoleService(session=session)

    try:
        orm_roles = await role_service.list_roles(
            membership_id=membership_id,
        )

    except RoleMembershipNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found",
        ) from error

    return [
        MembershipRoleRead.model_validate(role)
        for role in orm_roles
    ]


@router.delete(
    "/{membership_id}/roles/{role}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_role(
    membership_id: UUID,
    role: MembershipRoleType,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    role_service = MembershipRoleService(session=session)

    try:
        await role_service.remove_role(
            membership_id=membership_id,
            role=role,
        )

    except MembershipRoleNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        ) from error