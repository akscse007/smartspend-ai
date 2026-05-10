"""advanced features: budgets, savings goals, notifications, anomaly and indexes

Revision ID: 20260301_02
Revises: 20260228_01
Create Date: 2026-03-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260301_02"
down_revision: Union[str, None] = "20260228_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("anomaly_flag", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_transactions_anomaly_flag", "transactions", ["anomaly_flag"])
    op.create_index("ix_transactions_date_is_income", "transactions", ["date", "is_income"])
    op.create_index("ix_transactions_category_date", "transactions", ["category", "date"])

    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("monthly_limit", sa.Float(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "category", "month", "year", name="uq_budget_user_category_month_year"),
    )
    op.create_index("ix_budgets_user_id", "budgets", ["user_id"])
    op.create_index("ix_budgets_category_id", "budgets", ["category_id"])
    op.create_index("ix_budgets_category", "budgets", ["category"])
    op.create_index("ix_budgets_user_month_year", "budgets", ["user_id", "month", "year"])

    op.create_table(
        "savings_goals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("target_amount", sa.Float(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("current_saved", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_savings_goals_user_id", "savings_goals", ["user_id"])
    op.create_index("ix_savings_goals_user_target_date", "savings_goals", ["user_id", "target_date"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_type", "notifications", ["type"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])
    op.create_index("ix_notifications_user_read_created", "notifications", ["user_id", "is_read", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_read_created", table_name="notifications")
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_type", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_savings_goals_user_target_date", table_name="savings_goals")
    op.drop_index("ix_savings_goals_user_id", table_name="savings_goals")
    op.drop_table("savings_goals")

    op.drop_index("ix_budgets_user_month_year", table_name="budgets")
    op.drop_index("ix_budgets_category", table_name="budgets")
    op.drop_index("ix_budgets_category_id", table_name="budgets")
    op.drop_index("ix_budgets_user_id", table_name="budgets")
    op.drop_table("budgets")

    op.drop_index("ix_transactions_category_date", table_name="transactions")
    op.drop_index("ix_transactions_date_is_income", table_name="transactions")
    op.drop_index("ix_transactions_anomaly_flag", table_name="transactions")
    op.drop_column("transactions", "anomaly_flag")
