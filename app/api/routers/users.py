from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UserNotFoundError
from app.db.session import get_session
from app.schemas import UserRead
from app.services import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=list[UserRead],
    status_code=status.HTTP_200_OK,
)
async def get_all(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[UserRead]:
    user_service = UserService(session=session)
    orm_users = await user_service.list_of_users(limit=limit, offset=offset)
    response_users = [UserRead.model_validate(user) for user in orm_users]
    return response_users


@router.get(
    "/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
)
async def get_by_id(
    user_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserRead:
    user_service = UserService(session=session)
    try:
        orm_user = await user_service.get_user(user_id=user_id)
        return UserRead.model_validate(orm_user)
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error
