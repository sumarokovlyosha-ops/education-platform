from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        full_name: str,
        email: str,
        password_hash: str,
        is_active: bool = True,
    ) -> User:
        user = User(
            full_name=full_name,
            email=email,
            password_hash=password_hash,
            is_active=is_active,
        )

        self.session.add(user)

        await self.session.flush()
        await self.session.refresh(user)

        return user

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        statement = select(User).where(User.email == email)
        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

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
