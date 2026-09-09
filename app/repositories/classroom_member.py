from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classroom_member import ClassroomMember, ClassroomMemberRoleType


class ClassroomMemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        classroom_id: UUID,
        membership_id: UUID,
        role: ClassroomMemberRoleType,
    ) -> ClassroomMember:
        classroom_member = ClassroomMember(
            classroom_id=classroom_id,
            membership_id=membership_id,
            role=role,
        )

        self.session.add(classroom_member)
        await self.session.flush()
        await self.session.refresh(classroom_member)

        return classroom_member

    async def get(
        self,
        classroom_id: UUID,
        membership_id: UUID,
    ) -> ClassroomMember | None:
        stmt = select(ClassroomMember).where(
            ClassroomMember.classroom_id == classroom_id,
            ClassroomMember.membership_id == membership_id,
        )

        res = await self.session.execute(stmt)

        return res.scalar_one_or_none()

    async def list_by_classroom(
        self,
        classroom_id: UUID,
        limit: int,
        offset: int,
    ) -> Sequence[ClassroomMember]:
        stmt = (
            select(ClassroomMember)
            .where(ClassroomMember.classroom_id == classroom_id)
            .order_by(
                ClassroomMember.joined_at.desc(),
                ClassroomMember.membership_id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        res = await self.session.execute(stmt)

        return res.scalars().all()

    async def role_is_used(
        self,
        membership_id: UUID,
        role: ClassroomMemberRoleType,
    ) -> bool:
        stmt = select(
            exists().where(
                ClassroomMember.membership_id == membership_id,
                ClassroomMember.role == role,
            )
        )

        res = await self.session.execute(stmt)

        return bool(res.scalar_one())

    async def delete(
        self,
        classroom_member: ClassroomMember,
    ) -> None:
        await self.session.delete(classroom_member)
        await self.session.flush()
