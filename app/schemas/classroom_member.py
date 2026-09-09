from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.classroom_member import ClassroomMemberRoleType


class ClassroomMemberCreate(BaseModel):
    membership_id: UUID
    role: ClassroomMemberRoleType


class ClassroomMemberRead(BaseModel):
    classroom_id: UUID
    membership_id: UUID
    role: ClassroomMemberRoleType
    joined_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
