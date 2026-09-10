from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classroom import Classroom
from app.models.classroom_member import ClassroomMember, ClassroomMemberRoleType
from app.models.membership import Membership
from app.models.school import School
from app.models.user import User

pytestmark = pytest.mark.integration


async def create_dependencies(session: AsyncSession) -> tuple[Classroom, Membership]:
    user = User(
        full_name="Classroom Member",
        email="classroom.member@example.com",
        password_hash="not-used-in-this-test",
    )
    school = School(name="Classroom Member School")

    session.add_all([user, school])
    await session.flush()

    classroom = Classroom(
        school_id=school.id,
        name="10A",
        academic_year="2026/2027",
    )

    membership = Membership(
        user_id=user.id,
        school_id=school.id,
    )

    session.add_all([classroom, membership])
    await session.flush()

    return classroom, membership


async def get_classroom_member(
    session: AsyncSession,
    classroom_id: UUID,
    membership_id: UUID,
) -> ClassroomMember | None:
    stmt = select(ClassroomMember).where(
        ClassroomMember.classroom_id == classroom_id,
        ClassroomMember.membership_id == membership_id,
    )
    res = await session.execute(stmt)

    return res.scalar_one_or_none()


async def test_create_classroom_member(
    db_session: AsyncSession,
) -> None:
    classroom, membership = await create_dependencies(db_session)

    classroom_member = ClassroomMember(
        classroom_id=classroom.id,
        membership_id=membership.id,
        role=ClassroomMemberRoleType.STUDENT,
    )

    db_session.add(classroom_member)
    await db_session.flush()

    saved_member = await get_classroom_member(
        session=db_session,
        classroom_id=classroom.id,
        membership_id=membership.id,
    )

    assert saved_member is not None
    assert saved_member.role is ClassroomMemberRoleType.STUDENT
    assert saved_member.joined_at is not None


async def test_duplicate_classroom_member_is_rejected(
    db_session: AsyncSession,
) -> None:
    classroom, membership = await create_dependencies(db_session)

    db_session.add_all(
        [
            ClassroomMember(
                classroom_id=classroom.id,
                membership_id=membership.id,
                role=ClassroomMemberRoleType.STUDENT,
            ),
            ClassroomMember(
                classroom_id=classroom.id,
                membership_id=membership.id,
                role=ClassroomMemberRoleType.TEACHER,
            ),
        ]
    )

    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()


async def test_deleting_classroom_deletes_its_members(
    db_session: AsyncSession,
) -> None:
    classroom, membership = await create_dependencies(db_session)

    classroom_member = ClassroomMember(
        classroom_id=classroom.id,
        membership_id=membership.id,
        role=ClassroomMemberRoleType.STUDENT,
    )

    db_session.add(classroom_member)
    await db_session.flush()

    classroom_id = classroom.id
    membership_id = membership.id

    await db_session.delete(classroom)
    await db_session.flush()

    deleted_member = await get_classroom_member(
        session=db_session,
        classroom_id=classroom_id,
        membership_id=membership_id,
    )

    assert deleted_member is None


async def test_deleting_membership_deletes_classroom_member(
    db_session: AsyncSession,
) -> None:
    classroom, membership = await create_dependencies(db_session)

    classroom_member = ClassroomMember(
        classroom_id=classroom.id,
        membership_id=membership.id,
        role=ClassroomMemberRoleType.STUDENT,
    )

    db_session.add(classroom_member)
    await db_session.flush()

    classroom_id = classroom.id
    membership_id = membership.id

    await db_session.delete(membership)
    await db_session.flush()

    deleted_member = await get_classroom_member(
        session=db_session,
        classroom_id=classroom_id,
        membership_id=membership_id,
    )

    assert deleted_member is None
