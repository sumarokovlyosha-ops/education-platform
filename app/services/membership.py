from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import Membership
from app.repositories.membership import MembershipRepository
from app.repositories.school import SchoolRepository
from app.repositories.user import UserRepository


class MembershipNotFoundError(Exception):
    pass


class MembershipAlreadyExistsError(Exception):
    pass


class MembershipUserNotFoundError(Exception):
    pass


class MembershipSchoolNotFoundError(Exception):
    pass


class MembershipService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

        self.repository = MembershipRepository(session)
        self.user_repository = UserRepository(session)
        self.school_repository = SchoolRepository(session)

    async def create_membership(
        self,
        user_id: UUID,
        school_id: UUID,
    ) -> Membership:
        user = await self.user_repository.get_by_id(
            user_id=user_id,
        )

        if user is None:
            raise MembershipUserNotFoundError

        school = await self.school_repository.get_by_id(
            school_id=school_id,
        )

        if school is None:
            raise MembershipSchoolNotFoundError

        existing_membership = await self.repository.get_by_user_and_school(
            user_id=user_id,
            school_id=school_id,
        )

        if existing_membership is not None:
            raise MembershipAlreadyExistsError

        try:
            membership = await self.repository.create(
                user_id=user_id,
                school_id=school_id,
            )

            await self.session.commit()

        except IntegrityError:
            await self.session.rollback()
            raise MembershipAlreadyExistsError

        return membership

    async def get_membership(
        self,
        membership_id: UUID,
    ) -> Membership:
        membership = await self.repository.get_by_id(
            membership_id=membership_id,
        )

        if membership is None:
            raise MembershipNotFoundError

        return membership

    async def list_school_memberships(
        self,
        school_id: UUID,
    ) -> Sequence[Membership]:
        school = await self.school_repository.get_by_id(
            school_id=school_id,
        )

        if school is None:
            raise MembershipSchoolNotFoundError

        return await self.repository.list_by_school(
            school_id=school_id,
        )
