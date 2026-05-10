"""users auth and transaction ownership

Revision ID: 20260309_04
Revises: 20260309_03
Create Date: 2026-03-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260309_04"
down_revision: Union[str, None] = "20260309_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.execute(
        """
        INSERT INTO users (id, full_name, email, password_hash, is_active, created_at)
        VALUES (
            1,
            'Guest User',
            'guest@local',
            'system$disabled',
            true,
            NOW()
        )
        ON CONFLICT (id) DO NOTHING
        """
    )

    op.add_column("transactions", sa.Column("user_id", sa.Integer(), nullable=True, server_default="1"))
    op.execute("UPDATE transactions SET user_id = 1 WHERE user_id IS NULL")
    op.alter_column("transactions", "user_id", nullable=False, server_default=None)
    op.create_foreign_key("fk_transactions_user_id", "transactions", "users", ["user_id"], ["id"])
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])
    op.create_index("ix_transactions_user_date", "transactions", ["user_id", "date"])
    op.execute("ALTER TABLE transactions DROP CONSTRAINT IF EXISTS transactions_source_hash_key")
    op.create_unique_constraint("uq_transactions_user_source_hash", "transactions", ["user_id", "source_hash"])

    op.add_column("user_feedback", sa.Column("user_id", sa.Integer(), nullable=True, server_default="1"))
    op.execute("UPDATE user_feedback SET user_id = 1 WHERE user_id IS NULL")
    op.alter_column("user_feedback", "user_id", nullable=False, server_default=None)
    op.create_foreign_key("fk_user_feedback_user_id", "user_feedback", "users", ["user_id"], ["id"])
    op.create_index("ix_user_feedback_user_id", "user_feedback", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_feedback_user_id", table_name="user_feedback")
    op.drop_constraint("fk_user_feedback_user_id", "user_feedback", type_="foreignkey")
    op.drop_column("user_feedback", "user_id")

    op.drop_constraint("uq_transactions_user_source_hash", "transactions", type_="unique")
    op.drop_index("ix_transactions_user_date", table_name="transactions")
    op.drop_index("ix_transactions_user_id", table_name="transactions")
    op.drop_constraint("fk_transactions_user_id", "transactions", type_="foreignkey")
    op.drop_column("transactions", "user_id")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
