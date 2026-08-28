import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    Uuid,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.school import School


class Classroom(Base):
    __tablename__ = "classrooms"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    school_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("schools.id"),
    )
    name: Mapped[str] = mapped_column(
        String(50),
    )
    academic_year: Mapped[str] = mapped_column(
        String(9),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        server_default=true(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    school: Mapped["School"] = relationship(
        back_populates="classrooms",
    )

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "name",
            "academic_year",
            name="uq_classrooms_school_name_academic_year",
        ),
    )
