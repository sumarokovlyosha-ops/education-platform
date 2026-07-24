from typing import Sequence
from uuid import UUID
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.core.exceptions import UserNotFoundError
from app.models import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreateData


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = UserRepository(session)

    async def create_user(self, data: UserCreateData) -> User:
        password_hash = await asyncio.to_thread(
            hash_password,
            data.password,
        )
        try:
            user = await self.repository.create(
                full_name=data.full_name,
                password_hash=password_hash,
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return user

    async def verify_user_password(
        self,
        user: User,
        password: str,
    ) -> bool:
        return await asyncio.to_thread(
            verify_password,
            password,
            user.password_hash,
        )

    async def get_user(self, user_id: UUID) -> User:
        res = await self.repository.get_by_id(user_id=user_id)
        if res is None:
            raise UserNotFoundError(user_id=user_id)
        return res

    async def list_of_users(
        self,
        limit: int,
        offset: int,
    ) -> Sequence[User]:
        if not 1 <= limit <= 100:
            raise ValueError("limit должен быть от 1 до 100")

        if offset < 0:
            raise ValueError("offset не может быть отрицательным")

        return await self.repository.list_of_users(
            limit=limit,
            offset=offset,
        )
