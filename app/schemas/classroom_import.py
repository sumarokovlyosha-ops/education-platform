from pydantic import BaseModel, EmailStr, Field, field_validator


class ClassroomStudentImportRow(BaseModel):
    row_number: int = Field(ge=2)
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("full_name must not be empty")

        return normalized_value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()

        return value


class ClassroomStudentImportResult(BaseModel):
    total_rows: int
    created_users: int
    created_memberships: int
    created_membership_roles: int
    created_classroom_members: int
    existing_classroom_members: int
