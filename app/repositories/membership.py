from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import Membership


class MembershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: UUID,
        school_id: UUID,
    ) -> Membership:
        membership = Membership(
            user_id=user_id,
            school_id=school_id,
        )

        self.session.add(membership)

        await self.session.flush()
        await self.session.refresh(membership)

        return membership

    async def get_by_id(
        self,
        membership_id: UUID,
    ) -> Membership | None:
        statement = select(Membership).where(
            Membership.id == membership_id,
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_user_and_school(
        self,
        user_id: UUID,
        school_id: UUID,
    ) -> Membership | None:
        statement = select(Membership).where(
            Membership.user_id == user_id,
            Membership.school_id == school_id,
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def list_by_school(
        self,
        school_id: UUID,
    ) -> Sequence[Membership]:
        statement = (
            select(Membership)
            .where(Membership.school_id == school_id)
            .order_by(Membership.created_at.desc())
        )

        result = await self.session.execute(statement)

        return result.scalars().all()