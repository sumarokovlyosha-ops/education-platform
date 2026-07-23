from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, full_name: str, password_hash: str) -> User:

        user = User(full_name=full_name, password_hash=password_hash)

        self.session.add(user)

        await self.session.flush()
        await self.session.refresh(user)

        return user

    async def get_by_id(
        self,
        user_id: UUID,
    ) -> User | None:
        statement = select(User).where(User.id == user_id)
        res = await self.session.execute(statement)
        return res.scalar_one_or_none()

    async def list_of_users(
        self,
        limit: int,
        offset: int,
    ) -> Sequence[User]:
        statement = (
            select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
        )
        res = await self.session.execute(statement)
        return res.scalars().all()
