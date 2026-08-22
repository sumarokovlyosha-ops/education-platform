from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.membership_role import MembershipRoleType


class MembershipRoleCreate(BaseModel):
    role: MembershipRoleType


class MembershipRoleRead(BaseModel):
    membership_id: UUID
    role: MembershipRoleType

    model_config = ConfigDict(
        from_attributes=True,
    )