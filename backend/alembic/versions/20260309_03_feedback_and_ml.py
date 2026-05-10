"""feedback table for ml self-learning

Revision ID: 20260309_03
Revises: 20260301_02
Create Date: 2026-03-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260309_03"
down_revision: Union[str, None] = "20260301_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transaction_id", sa.Integer(), sa.ForeignKey("transactions.id"), nullable=True),
        sa.Column("transaction_text", sa.String(length=300), nullable=False),
        sa.Column("predicted_category", sa.String(length=100), nullable=False),
        sa.Column("corrected_category", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_user_feedback_transaction_id", "user_feedback", ["transaction_id"])
    op.create_index("ix_user_feedback_created_at", "user_feedback", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_user_feedback_created_at", table_name="user_feedback")
    op.drop_index("ix_user_feedback_transaction_id", table_name="user_feedback")
    op.drop_table("user_feedback")
