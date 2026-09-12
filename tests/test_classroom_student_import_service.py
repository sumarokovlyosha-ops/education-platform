from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.classroom import Classroom
from app.models.classroom_member import (
    ClassroomMember,
    ClassroomMemberRoleType,
)
from app.models.membership import Membership
from app.models.membership_role import (
    MembershipRole,
    MembershipRoleType,
)
from app.models.school import School
from app.models.user import User
from app.schemas.classroom_import import ClassroomStudentImportRow
from app.services.classroom_student_import import (
    ClassroomStudentImportRowConflictError,
    ClassroomStudentImportService,
    ImportClassroomInactiveError,
    ImportClassroomNotFoundError,
)

pytestmark = pytest.mark.integration


def import_row(
    row_number: int,
    full_name: str,
    email: str,
) -> ClassroomStudentImportRow:
    return ClassroomStudentImportRow.model_validate(
        {
            "row_number": row_number,
            "full_name": full_name,
            "email": email,
        }
    )


async def create_school_and_classroom(
    session: AsyncSession,
    *,
    classroom_is_active: bool = True,
) -> Classroom:
    school = School(name=f"Import School {uuid4()}")
    session.add(school)
    await session.flush()

    classroom = Classroom(
        school_id=school.id,
        name="10A",
        academic_year="2026/2027",
        is_active=classroom_is_active,
    )
    session.add(classroom)
    await session.flush()

    return classroom


async def test_import_creates_missing_student_relations(
    db_session: AsyncSession,
) -> None:
    classroom = await create_school_and_classroom(db_session)
    service = ClassroomStudentImportService(db_session)

    rows = [
        import_row(
            row_number=2,
            full_name="New Student",
            email="new.student@example.com",
        )
    ]

    result = await service.import_students(
        classroom_id=classroom.id,
        rows=rows,
    )

    assert result.total_rows == 1
    assert result.created_users == 1
    assert result.created_memberships == 1
    assert result.created_membership_roles == 1
    assert result.created_classroom_members == 1
    assert result.existing_classroom_members == 0

    user_result = await db_session.execute(
        select(User).where(User.email == "new.student@example.com")
    )
    user = user_result.scalar_one()

    assert user.full_name == "New Student"
    assert user.is_active is False
    assert (
        verify_password(
            "any-password",
            user.password_hash,
        )
        is False
    )

    membership_result = await db_session.execute(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.school_id == classroom.school_id,
        )
    )
    membership = membership_result.scalar_one()

    role = await db_session.get(
        MembershipRole,
        (membership.id, MembershipRoleType.STUDENT),
    )
    classroom_member = await db_session.get(
        ClassroomMember,
        (classroom.id, membership.id),
    )

    assert role is not None
    assert classroom_member is not None
    assert classroom_member.role == ClassroomMemberRoleType.STUDENT


async def test_import_is_idempotent(
    db_session: AsyncSession,
) -> None:
    classroom = await create_school_and_classroom(db_session)
    service = ClassroomStudentImportService(db_session)

    rows = [
        import_row(
            row_number=2,
            full_name="Repeated Student",
            email="repeated.student@example.com",
        )
    ]

    first_result = await service.import_students(
        classroom_id=classroom.id,
        rows=rows,
    )
    second_result = await service.import_students(
        classroom_id=classroom.id,
        rows=rows,
    )

    assert first_result.created_classroom_members == 1

    assert second_result.created_users == 0
    assert second_result.created_memberships == 0
    assert second_result.created_membership_roles == 0
    assert second_result.created_classroom_members == 0
    assert second_result.existing_classroom_members == 1


async def test_import_reuses_user_without_overwriting_name(
    db_session: AsyncSession,
) -> None:
    classroom = await create_school_and_classroom(db_session)

    user = User(
        full_name="Stored Name",
        email="existing.student@example.com",
        password_hash="not-used-in-this-test",
    )
    db_session.add(user)
    await db_session.flush()

    service = ClassroomStudentImportService(db_session)

    result = await service.import_students(
        classroom_id=classroom.id,
        rows=[
            import_row(
                row_number=2,
                full_name="Different Excel Name",
                email="existing.student@example.com",
            )
        ],
    )

    assert result.created_users == 0
    assert user.full_name == "Stored Name"


async def test_import_rolls_back_all_rows_on_conflict(
    db_session: AsyncSession,
) -> None:
    classroom = await create_school_and_classroom(db_session)

    blocked_user = User(
        full_name="Blocked Student",
        email="blocked.student@example.com",
        password_hash="not-used-in-this-test",
    )
    db_session.add(blocked_user)
    await db_session.flush()

    inactive_membership = Membership(
        user_id=blocked_user.id,
        school_id=classroom.school_id,
        is_active=False,
    )
    db_session.add(inactive_membership)
    await db_session.commit()

    service = ClassroomStudentImportService(db_session)

    with pytest.raises(ClassroomStudentImportRowConflictError) as error_info:
        await service.import_students(
            classroom_id=classroom.id,
            rows=[
                import_row(
                    row_number=2,
                    full_name="Must Be Rolled Back",
                    email="rollback.student@example.com",
                ),
                import_row(
                    row_number=3,
                    full_name="Blocked Student",
                    email="blocked.student@example.com",
                ),
            ],
        )

    assert error_info.value.row_number == 3
    assert error_info.value.email == "blocked.student@example.com"
    assert error_info.value.message == "School membership is inactive"

    rolled_back_user_result = await db_session.execute(
        select(User).where(User.email == "rollback.student@example.com")
    )

    assert rolled_back_user_result.scalar_one_or_none() is None


async def test_import_does_not_replace_teacher_role(
    db_session: AsyncSession,
) -> None:
    classroom = await create_school_and_classroom(db_session)

    user = User(
        full_name="Existing Teacher",
        email="teacher@example.com",
        password_hash="not-used-in-this-test",
    )
    db_session.add(user)
    await db_session.flush()

    membership = Membership(
        user_id=user.id,
        school_id=classroom.school_id,
    )
    db_session.add(membership)
    await db_session.flush()

    membership_id = membership.id

    db_session.add_all(
        [
            MembershipRole(
                membership_id=membership_id,
                role=MembershipRoleType.TEACHER,
            ),
            ClassroomMember(
                classroom_id=classroom.id,
                membership_id=membership_id,
                role=ClassroomMemberRoleType.TEACHER,
            ),
        ]
    )
    await db_session.commit()

    service = ClassroomStudentImportService(db_session)

    with pytest.raises(ClassroomStudentImportRowConflictError) as error_info:
        await service.import_students(
            classroom_id=classroom.id,
            rows=[
                import_row(
                    row_number=2,
                    full_name="Existing Teacher",
                    email="teacher@example.com",
                )
            ],
        )

    assert error_info.value.message == ("User is already a teacher in this classroom")

    student_role = await db_session.get(
        MembershipRole,
        (membership_id, MembershipRoleType.STUDENT),
    )

    assert student_role is None


async def test_import_rejects_unknown_classroom(
    db_session: AsyncSession,
) -> None:
    service = ClassroomStudentImportService(db_session)

    with pytest.raises(ImportClassroomNotFoundError):
        await service.import_students(
            classroom_id=uuid4(),
            rows=[],
        )


async def test_import_rejects_inactive_classroom(
    db_session: AsyncSession,
) -> None:
    classroom = await create_school_and_classroom(
        db_session,
        classroom_is_active=False,
    )
    service = ClassroomStudentImportService(db_session)

    with pytest.raises(ImportClassroomInactiveError):
        await service.import_students(
            classroom_id=classroom.id,
            rows=[],
        )
