from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas import UserCreateData, UserRead
from app.services.user import UserAlreadyExistsError, UserService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: UserCreateData,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserRead:
    user_service = UserService(session=session)

    try:
        orm_user = await user_service.create_user(data=data)
    except UserAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        ) from error

    return UserRead.model_validate(orm_user)
