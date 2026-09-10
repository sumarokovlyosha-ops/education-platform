from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classroom_member import ClassroomMemberRoleType
from app.models.membership_role import (
    MembershipRole,
    MembershipRoleType,
)
from app.repositories.classroom_member import ClassroomMemberRepository
from app.repositories.membership import MembershipRepository
from app.repositories.membership_role import MembershipRoleRepository


class MembershipRoleAlreadyExistsError(Exception):
    pass


class MembershipRoleNotFoundError(Exception):
    pass


class MembershipRoleInUseError(Exception):
    pass


class RoleMembershipNotFoundError(Exception):
    pass


class MembershipRoleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

        self.repository = MembershipRoleRepository(session)
        self.membership_repository = MembershipRepository(session)
        self.classroom_member_repository = ClassroomMemberRepository(session)

    async def add_role(
        self,
        membership_id: UUID,
        role: MembershipRoleType,
    ) -> MembershipRole:
        membership = await self.membership_repository.get_by_id(
            membership_id=membership_id,
        )

        if membership is None:
            raise RoleMembershipNotFoundError

        existing_role = await self.repository.get(
            membership_id=membership_id,
            role=role,
        )

        if existing_role is not None:
            raise MembershipRoleAlreadyExistsError

        try:
            membership_role = await self.repository.create(
                membership_id=membership_id,
                role=role,
            )

            await self.session.commit()

        except IntegrityError:
            await self.session.rollback()
            raise MembershipRoleAlreadyExistsError

        return membership_role

    async def remove_role(
        self,
        membership_id: UUID,
        role: MembershipRoleType,
    ) -> None:
        membership_role = await self.repository.get(
            membership_id=membership_id,
            role=role,
        )

        if membership_role is None:
            raise MembershipRoleNotFoundError

        if role in {MembershipRoleType.STUDENT, MembershipRoleType.TEACHER}:
            classroom_role = ClassroomMemberRoleType(role.value)
            role_is_used = await self.classroom_member_repository.role_is_used(
                membership_id=membership_id,
                role=classroom_role,
            )

            if role_is_used:
                raise MembershipRoleInUseError

        await self.repository.delete(membership_role)
        await self.session.commit()

    async def list_roles(
        self,
        membership_id: UUID,
    ) -> Sequence[MembershipRole]:
        membership = await self.membership_repository.get_by_id(
            membership_id=membership_id,
        )

        if membership is None:
            raise RoleMembershipNotFoundError

        return await self.repository.list_by_membership(
            membership_id=membership_id,
        )
