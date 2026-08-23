from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership_role import (
    MembershipRole,
    MembershipRoleType,
)


class MembershipRoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        membership_id: UUID,
        role: MembershipRoleType,
    ) -> MembershipRole:
        membership_role = MembershipRole(
            membership_id=membership_id,
            role=role,
        )

        self.session.add(membership_role)
        await self.session.flush()

        return membership_role

    async def get(
        self,
        membership_id: UUID,
        role: MembershipRoleType,
    ) -> MembershipRole | None:
        statement = select(MembershipRole).where(
            MembershipRole.membership_id == membership_id,
            MembershipRole.role == role,
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def list_by_membership(
        self,
        membership_id: UUID,
    ) -> Sequence[MembershipRole]:
        statement = select(MembershipRole).where(
            MembershipRole.membership_id == membership_id,
        )

        result = await self.session.execute(statement)

        return result.scalars().all()

    async def delete(
        self,
        membership_role: MembershipRole,
    ) -> None:
        await self.session.delete(membership_role)
        await self.session.flush()