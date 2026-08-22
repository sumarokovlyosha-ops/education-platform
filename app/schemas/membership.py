from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MembershipCreate(BaseModel):
    user_id: UUID


class MembershipRead(BaseModel):
    id: UUID
    user_id: UUID
    school_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )