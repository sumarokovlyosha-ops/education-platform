from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas import UserCreateData, UserRead
from app.services import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreateData, session: Annotated[AsyncSession, Depends(get_session)]
) -> UserRead:
    user_service = UserService(session=session)
    orm_user = await user_service.create_user(data=data)
    return UserRead.model_validate(orm_user)
