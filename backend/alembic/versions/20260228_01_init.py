"""initial schema

Revision ID: 20260228_01
Revises:
Create Date: 2026-02-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260228_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(length=300), nullable=False),
        sa.Column("clean_description", sa.String(length=300), nullable=False),
        sa.Column("merchant", sa.String(length=150), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("amount_inr", sa.Float(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("prediction_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("is_income", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_subscription", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("recurrence", sa.String(length=20), nullable=False, server_default="none"),
        sa.Column("source_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_transactions_date", "transactions", ["date"])
    op.create_index("ix_transactions_category", "transactions", ["category"])
    op.create_index("ix_transactions_merchant", "transactions", ["merchant"])

    op.create_table(
        "category_overrides",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transaction_id", sa.Integer(), sa.ForeignKey("transactions.id"), nullable=False),
        sa.Column("previous_category", sa.String(length=100), nullable=False),
        sa.Column("new_category", sa.String(length=100), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "budget_recommendations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("month", sa.String(length=7), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("current_spend", sa.Float(), nullable=False),
        sa.Column("recommended_budget", sa.Float(), nullable=False),
        sa.Column("potential_savings", sa.Float(), nullable=False),
        sa.Column("advice", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("month", "category", name="uq_budget_month_category"),
    )

    op.create_table(
        "monthly_summaries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("month", sa.String(length=7), nullable=False, unique=True),
        sa.Column("total_income", sa.Float(), nullable=False),
        sa.Column("total_expense", sa.Float(), nullable=False),
        sa.Column("net_savings", sa.Float(), nullable=False),
        sa.Column("health_score", sa.Float(), nullable=False),
        sa.Column("ai_summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("monthly_summaries")
    op.drop_table("budget_recommendations")
    op.drop_table("category_overrides")
    op.drop_index("ix_transactions_merchant", table_name="transactions")
    op.drop_index("ix_transactions_category", table_name="transactions")
    op.drop_index("ix_transactions_date", table_name="transactions")
    op.drop_table("transactions")
