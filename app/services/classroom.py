from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classroom import Classroom
from app.repositories.classroom import ClassroomRepository
from app.repositories.school import SchoolRepository
from app.schemas.classroom import ClassroomCreate


class ClassroomNotFoundError(Exception):
    pass


class ClassroomAlreadyExistsError(Exception):
    pass


class ClassroomSchoolNotFoundError(Exception):
    pass


class ClassroomService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ClassroomRepository(session)
        self.school_repository = SchoolRepository(session)

    async def create_classroom(
        self,
        school_id: UUID,
        data: ClassroomCreate,
    ) -> Classroom:
        school = await self.school_repository.get_by_id(
            school_id=school_id,
        )

        if school is None:
            raise ClassroomSchoolNotFoundError

        existing_classroom = await self.repository.get_by_school_name_and_year(
            school_id=school_id,
            name=data.name,
            academic_year=data.academic_year,
        )

        if existing_classroom is not None:
            raise ClassroomAlreadyExistsError

        try:
            classroom = await self.repository.create(
                school_id=school_id,
                name=data.name,
                academic_year=data.academic_year,
            )

            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ClassroomAlreadyExistsError from None

        return classroom

    async def get_classroom(
        self,
        classroom_id: UUID,
    ) -> Classroom:
        classroom = await self.repository.get_by_id(
            classroom_id=classroom_id,
        )

        if classroom is None:
            raise ClassroomNotFoundError

        return classroom

    async def list_school_classrooms(
        self,
        school_id: UUID,
        limit: int,
        offset: int,
    ) -> Sequence[Classroom]:
        school = await self.school_repository.get_by_id(
            school_id=school_id,
        )

        if school is None:
            raise ClassroomSchoolNotFoundError

        return await self.repository.list_by_school(
            school_id=school_id,
            limit=limit,
            offset=offset,
        )
