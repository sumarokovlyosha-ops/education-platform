"""add classroom members

Revision ID: 53eaa1cc23bb
Revises: 89176bc700f9
Create Date: 2026-09-07 17:10:49.231214

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "53eaa1cc23bb"
down_revision: str | Sequence[str] | None = "89176bc700f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "classroom_members",
        sa.Column("classroom_id", sa.Uuid(), nullable=False),
        sa.Column("membership_id", sa.Uuid(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("student", "teacher", name="classroom_member_role_type"),
            nullable=False,
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["classroom_id"], ["classrooms.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["membership_id"], ["memberships.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("classroom_id", "membership_id"),
    )
    op.create_index(
        op.f("ix_classroom_members_membership_id"),
        "classroom_members",
        ["membership_id"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_classroom_members_membership_id"),
        table_name="classroom_members",
    )
    op.drop_table("classroom_members")

    sa.Enum(
        "student",
        "teacher",
        name="classroom_member_role_type",
    ).drop(op.get_bind())
    # ### end Alembic commands ###
