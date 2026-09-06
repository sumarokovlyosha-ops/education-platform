from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.classroom import ClassroomCache
from app.models.classroom import Classroom
from app.repositories.classroom import ClassroomRepository
from app.repositories.school import SchoolRepository
from app.schemas.classroom import ClassroomCreate, ClassroomRead


class ClassroomNotFoundError(Exception):
    pass


class ClassroomAlreadyExistsError(Exception):
    pass


class ClassroomSchoolNotFoundError(Exception):
    pass


class ClassroomService:
    def __init__(
        self,
        session: AsyncSession,
        cache: ClassroomCache,
    ) -> None:
        self.session = session
        self.cache = cache
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

        await self.cache.invalidate_school_classrooms(school_id)

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
    ) -> list[ClassroomRead]:
        school = await self.school_repository.get_by_id(
            school_id=school_id,
        )

        if school is None:
            raise ClassroomSchoolNotFoundError

        cache_result = await self.cache.get_school_classrooms(
            school_id=school_id,
            limit=limit,
            offset=offset,
        )

        if cache_result.classrooms is not None:
            return cache_result.classrooms

        orm_classrooms = await self.repository.list_by_school(
            school_id=school_id,
            limit=limit,
            offset=offset,
        )

        classrooms = [
            ClassroomRead.model_validate(classroom) for classroom in orm_classrooms
        ]

        if cache_result.generation is not None:
            await self.cache.set_school_classrooms(
                school_id=school_id,
                generation=cache_result.generation,
                limit=limit,
                offset=offset,
                classrooms=classrooms,
            )

        return classrooms
