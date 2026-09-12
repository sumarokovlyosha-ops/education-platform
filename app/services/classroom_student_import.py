from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import make_unusable_password_hash
from app.models.classroom_member import ClassroomMemberRoleType
from app.models.membership_role import MembershipRoleType
from app.repositories.classroom import ClassroomRepository
from app.repositories.classroom_member import ClassroomMemberRepository
from app.repositories.membership import MembershipRepository
from app.repositories.membership_role import MembershipRoleRepository
from app.repositories.user import UserRepository
from app.schemas.classroom_import import (
    ClassroomStudentImportResult,
    ClassroomStudentImportRow,
)


class ImportClassroomNotFoundError(Exception):
    pass


class ImportClassroomInactiveError(Exception):
    pass


class ClassroomStudentImportRowConflictError(Exception):
    def __init__(
        self,
        row_number: int,
        email: str,
        message: str,
    ) -> None:
        self.row_number = row_number
        self.email = email
        self.message = message
        super().__init__(f"Row {row_number} ({email}): {message}")


class ClassroomStudentImportConcurrentChangeError(Exception):
    pass


class ClassroomStudentImportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repository = UserRepository(session)
        self.classroom_repository = ClassroomRepository(session)
        self.membership_repository = MembershipRepository(session)
        self.membership_role_repository = MembershipRoleRepository(session)
        self.classroom_member_repository = ClassroomMemberRepository(session)

    async def import_students(
        self,
        classroom_id: UUID,
        rows: Sequence[ClassroomStudentImportRow],
    ) -> ClassroomStudentImportResult:
        classroom = await self.classroom_repository.get_by_id(
            classroom_id=classroom_id,
        )

        if classroom is None:
            raise ImportClassroomNotFoundError

        if not classroom.is_active:
            raise ImportClassroomInactiveError

        created_users = 0
        created_memberships = 0
        created_membership_roles = 0
        created_classroom_members = 0
        existing_classroom_members = 0

        try:
            for row in rows:
                email = str(row.email)

                user = await self.user_repository.get_by_email(
                    email=email,
                )

                if user is None:
                    user = await self.user_repository.create(
                        full_name=row.full_name,
                        email=email,
                        password_hash=make_unusable_password_hash(),
                        is_active=False,
                    )
                    created_users += 1

                membership = await self.membership_repository.get_by_user_and_school(
                    user_id=user.id,
                    school_id=classroom.school_id,
                )

                if membership is None:
                    membership = await self.membership_repository.create(
                        user_id=user.id,
                        school_id=classroom.school_id,
                    )
                    created_memberships += 1
                elif not membership.is_active:
                    raise ClassroomStudentImportRowConflictError(
                        row_number=row.row_number,
                        email=email,
                        message="School membership is inactive",
                    )

                student_role = await self.membership_role_repository.get(
                    membership_id=membership.id,
                    role=MembershipRoleType.STUDENT,
                )

                if student_role is None:
                    await self.membership_role_repository.create(
                        membership_id=membership.id,
                        role=MembershipRoleType.STUDENT,
                    )
                    created_membership_roles += 1

                classroom_member = await self.classroom_member_repository.get(
                    classroom_id=classroom.id,
                    membership_id=membership.id,
                )

                if classroom_member is None:
                    await self.classroom_member_repository.create(
                        classroom_id=classroom.id,
                        membership_id=membership.id,
                        role=ClassroomMemberRoleType.STUDENT,
                    )
                    created_classroom_members += 1
                elif classroom_member.role == ClassroomMemberRoleType.STUDENT:
                    existing_classroom_members += 1
                else:
                    raise ClassroomStudentImportRowConflictError(
                        row_number=row.row_number,
                        email=email,
                        message=("User is already a teacher in this classroom"),
                    )

            await self.session.commit()
        except IntegrityError as error:
            await self.session.rollback()
            raise ClassroomStudentImportConcurrentChangeError from error
        except Exception:
            await self.session.rollback()
            raise

        return ClassroomStudentImportResult(
            total_rows=len(rows),
            created_users=created_users,
            created_memberships=created_memberships,
            created_membership_roles=created_membership_roles,
            created_classroom_members=created_classroom_members,
            existing_classroom_members=existing_classroom_members,
        )
