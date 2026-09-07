import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.classroom import Classroom
    from app.models.membership import Membership


class ClassroomMemberRoleType(StrEnum):
    STUDENT = "student"
    TEACHER = "teacher"


class ClassroomMember(Base):
    __tablename__ = "classroom_members"

    classroom_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        primary_key=True,
    )

    membership_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("memberships.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    role: Mapped[ClassroomMemberRoleType] = mapped_column(
        Enum(
            ClassroomMemberRoleType,
            name="classroom_member_role_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    classroom: Mapped["Classroom"] = relationship(
        back_populates="members",
    )

    membership: Mapped["Membership"] = relationship(back_populates="classroom_members")
