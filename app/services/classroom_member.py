from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classroom_member import ClassroomMember, ClassroomMemberRoleType
from app.models.membership_role import MembershipRoleType
from app.repositories.classroom import ClassroomRepository
from app.repositories.classroom_member import ClassroomMemberRepository
from app.repositories.membership import MembershipRepository
from app.repositories.membership_role import MembershipRoleRepository
from app.schemas.classroom_member import ClassroomMemberCreate


class MemberClassroomNotFoundError(Exception):
    pass


class MemberMembershipNotFoundError(Exception):
    pass


class ClassroomMemberAlreadyExistsError(Exception):
    pass


class ClassroomMemberNotFoundError(Exception):
    pass


class ClassroomMemberSchoolMismatchError(Exception):
    pass


class ClassroomMemberInactiveClassroomError(Exception):
    pass


class ClassroomMemberInactiveMembershipError(Exception):
    pass


class ClassroomMemberRoleRequiredError(Exception):
    pass


REQUIRED_MEMBERSHIP_ROLES: dict[
    ClassroomMemberRoleType,
    MembershipRoleType,
] = {
    ClassroomMemberRoleType.STUDENT: MembershipRoleType.STUDENT,
    ClassroomMemberRoleType.TEACHER: MembershipRoleType.TEACHER,
}


class ClassroomMemberService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ClassroomMemberRepository(session)
        self.classroom_repository = ClassroomRepository(session)
        self.membership_repository = MembershipRepository(session)
        self.membership_role_repository = MembershipRoleRepository(session)

    async def add_member(
        self,
        classroom_id: UUID,
        data: ClassroomMemberCreate,
    ) -> ClassroomMember:
        classroom = await self.classroom_repository.get_by_id(
            classroom_id=classroom_id,
        )

        if classroom is None:
            raise MemberClassroomNotFoundError

        membership = await self.membership_repository.get_by_id(
            membership_id=data.membership_id,
        )

        if membership is None:
            raise MemberMembershipNotFoundError

        if classroom.school_id != membership.school_id:
            raise ClassroomMemberSchoolMismatchError

        if not classroom.is_active:
            raise ClassroomMemberInactiveClassroomError

        if not membership.is_active:
            raise ClassroomMemberInactiveMembershipError

        required_role = REQUIRED_MEMBERSHIP_ROLES[data.role]
        membership_role = await self.membership_role_repository.get(
            membership_id=membership.id,
            role=required_role,
        )

        if membership_role is None:
            raise ClassroomMemberRoleRequiredError

        existing_member = await self.repository.get(
            classroom_id=classroom_id,
            membership_id=membership.id,
        )

        if existing_member is not None:
            raise ClassroomMemberAlreadyExistsError

        try:
            classroom_member = await self.repository.create(
                classroom_id=classroom_id,
                membership_id=membership.id,
                role=data.role,
            )
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ClassroomMemberAlreadyExistsError from None

        return classroom_member

    async def list_members(
        self,
        classroom_id: UUID,
        limit: int,
        offset: int,
    ) -> Sequence[ClassroomMember]:
        classroom = await self.classroom_repository.get_by_id(
            classroom_id=classroom_id,
        )

        if classroom is None:
            raise MemberClassroomNotFoundError

        return await self.repository.list_by_classroom(
            classroom_id=classroom_id,
            limit=limit,
            offset=offset,
        )

    async def remove_member(
        self,
        classroom_id: UUID,
        membership_id: UUID,
    ) -> None:
        classroom_member = await self.repository.get(
            classroom_id=classroom_id,
            membership_id=membership_id,
        )

        if classroom_member is None:
            raise ClassroomMemberNotFoundError

        await self.repository.delete(classroom_member)
        await self.session.commit()
