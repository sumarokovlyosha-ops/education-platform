from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.school import School


class SchoolRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        name: str,
    ) -> School:
        school = School(
            name=name,
        )

        self.session.add(school)

        await self.session.flush()
        await self.session.refresh(school)

        return school

    async def get_by_id(
        self,
        school_id: UUID,
    ) -> School | None:
        statement = select(School).where(
            School.id == school_id,
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def list_of_schools(
        self,
        limit: int,
        offset: int,
    ) -> Sequence[School]:
        statement = (
            select(School)
            .order_by(School.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(statement)

        return result.scalars().all()
