import uuid
from datetime import datetime

from sqlalchemy import (
    Uuid,
    String,
    Boolean,
    DateTime,
    func,
    true,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
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
