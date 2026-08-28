from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classroom import Classroom


class ClassroomRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        school_id: UUID,
        name: str,
        academic_year: str,
    ) -> Classroom:
        classroom = Classroom(
            school_id=school_id,
            name=name,
            academic_year=academic_year,
        )

        self.session.add(classroom)

        await self.session.flush()
        await self.session.refresh(classroom)

        return classroom

    async def get_by_id(
        self,
        classroom_id: UUID,
    ) -> Classroom | None:
        statement = select(Classroom).where(
            Classroom.id == classroom_id,
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_school_name_and_year(
        self,
        school_id: UUID,
        name: str,
        academic_year: str,
    ) -> Classroom | None:
        statement = select(Classroom).where(
            Classroom.school_id == school_id,
            Classroom.name == name,
            Classroom.academic_year == academic_year,
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def list_by_school(
        self,
        school_id: UUID,
        limit: int,
        offset: int,
    ) -> Sequence[Classroom]:
        statement = (
            select(Classroom)
            .where(Classroom.school_id == school_id)
            .order_by(
                Classroom.created_at.desc(),
                Classroom.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(statement)

        return result.scalars().all()
