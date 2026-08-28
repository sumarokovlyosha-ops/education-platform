from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClassroomCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=50,
    )
    academic_year: str

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("name must not be empty")

        return normalized_value

    @field_validator("academic_year")
    @classmethod
    def validate_academic_year(cls, value: str) -> str:
        normalized_value = value.strip()
        parts = normalized_value.split("/")

        if len(parts) != 2 or any(
            len(part) != 4 or not part.isdigit() for part in parts
        ):
            raise ValueError("academic_year must use YYYY/YYYY format")

        start_year, end_year = map(int, parts)

        if end_year != start_year + 1:
            raise ValueError(
                "academic_year end must be one year after its start",
            )

        return normalized_value


class ClassroomRead(BaseModel):
    id: UUID
    school_id: UUID
    name: str
    academic_year: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
