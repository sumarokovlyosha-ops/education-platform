import uuid
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.membership import Membership


class MembershipRoleType(StrEnum):
    STUDENT = "student"
    TEACHER = "teacher"
    SCHEDULE_MANAGER = "schedule_manager"
    ADMIN = "admin"


class MembershipRole(Base):
    __tablename__ = "membership_roles"

    membership_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("memberships.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[MembershipRoleType] = mapped_column(
        Enum(
            MembershipRoleType,
            name="membership_role_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        primary_key=True,
    )

    membership: Mapped["Membership"] = relationship(
        back_populates="roles",
    )
