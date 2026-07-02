"""Widen models.location to fit real URLs and module paths

Revision ID: 56df91dbb3bf
Revises: 464c9b05374b
Create Date: 2026-07-03 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "56df91dbb3bf"
down_revision: Union[str, None] = "464c9b05374b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("models") as batch_op:
        batch_op.alter_column(
            "location",
            existing_type=sa.String(length=50),
            type_=sa.String(length=500),
            existing_nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("models") as batch_op:
        batch_op.alter_column(
            "location",
            existing_type=sa.String(length=500),
            type_=sa.String(length=50),
            existing_nullable=True,
        )
