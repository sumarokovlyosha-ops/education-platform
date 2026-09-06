"""add schools memberships and roles

Revision ID: 0f013d8d5b88
Revises: 7ea781a97a00
Create Date: 2026-08-22 22:13:38.264543

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0f013d8d5b88"
down_revision: str | Sequence[str] | None = "7ea781a97a00"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "schools",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "memberships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "school_id", name="uq_memberships_user_school"),
    )
    op.create_table(
        "membership_roles",
        sa.Column("membership_id", sa.Uuid(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "student",
                "teacher",
                "schedule_manager",
                "admin",
                name="membership_role_type",
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["membership_id"], ["memberships.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("membership_id", "role"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("membership_roles")

    sa.Enum(
        "student",
        "teacher",
        "schedule_manager",
        "admin",
        name="membership_role_type",
    ).drop(op.get_bind())

    op.drop_table("memberships")
    op.drop_table("schools")
