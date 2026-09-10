"""add user emails

Revision ID: e0844c4dc8a5
Revises: 53eaa1cc23bb
Create Date: 2026-09-10 23:54:37.986246

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e0844c4dc8a5"
down_revision: str | Sequence[str] | None = "53eaa1cc23bb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "email",
            sa.String(length=320),
            nullable=True,
        ),
    )

    op.execute(
        sa.text(
            """
            UPDATE users
            SET email = 'legacy-' || id::text || '@example.com'
            WHERE email IS NULL
            """
        )
    )

    op.alter_column(
        "users",
        "email",
        existing_type=sa.String(length=320),
        nullable=False,
    )

    op.create_unique_constraint(
        "uq_users_email",
        "users",
        ["email"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "uq_users_email",
        "users",
        type_="unique",
    )

    op.drop_column(
        "users",
        "email",
    )
