"""instant savings entries

Revision ID: 20260310_06
Revises: 20260310_05
Create Date: 2026-03-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260310_06"
down_revision: Union[str, None] = "20260310_05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "instant_savings_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("wishlist_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["wishlist_id"], ["wishlist_items.id"], name="fk_instant_savings_entries_wishlist_id"),
    )
    op.create_index("ix_instant_savings_entries_user_id", "instant_savings_entries", ["user_id"])
    op.create_index("ix_instant_savings_entries_wishlist_id", "instant_savings_entries", ["wishlist_id"])
    op.create_index(
        "ix_instant_savings_entries_user_created",
        "instant_savings_entries",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_instant_savings_entries_user_wishlist_created",
        "instant_savings_entries",
        ["user_id", "wishlist_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_instant_savings_entries_user_wishlist_created", table_name="instant_savings_entries")
    op.drop_index("ix_instant_savings_entries_user_created", table_name="instant_savings_entries")
    op.drop_index("ix_instant_savings_entries_wishlist_id", table_name="instant_savings_entries")
    op.drop_index("ix_instant_savings_entries_user_id", table_name="instant_savings_entries")
    op.drop_table("instant_savings_entries")
