from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class UserCreateData(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    password_hash: str = Field(min_length=1, max_length=255)
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )


class UserRead(BaseModel):
    id: UUID
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
