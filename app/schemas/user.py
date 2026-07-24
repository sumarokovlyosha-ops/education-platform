from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


class UserCreateData(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128, repr=False)
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("full_name must not be empty")

        return normalized_value


class UserRead(BaseModel):
    id: UUID
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
