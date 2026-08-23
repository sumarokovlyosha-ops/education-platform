from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.school import School
from app.repositories.school import SchoolRepository
from app.schemas.school import SchoolCreate


class SchoolNotFoundError(Exception):
    pass


class SchoolService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = SchoolRepository(session)

    async def create_school(
        self,
        data: SchoolCreate,
    ) -> School:
        school = await self.repository.create(
            name=data.name,
        )

        await self.session.commit()

        return school

    async def get_school(
        self,
        school_id: UUID,
    ) -> School:
        school = await self.repository.get_by_id(
            school_id=school_id,
        )

        if school is None:
            raise SchoolNotFoundError

        return school

    async def list_schools(
        self,
        limit: int,
        offset: int,
    ) -> Sequence[School]:
        return await self.repository.list_of_schools(
            limit=limit,
            offset=offset,
        )
