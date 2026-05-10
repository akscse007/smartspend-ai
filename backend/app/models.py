from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email", "email", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("user_id", "source_hash", name="uq_transactions_user_source_hash"),
        Index("ix_transactions_user_date", "user_id", "date"),
        Index("ix_transactions_date_is_income", "date", "is_income"),
        Index("ix_transactions_category_date", "category", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True, default=1)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    clean_description: Mapped[str] = mapped_column(String(300), nullable=False)
    merchant: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")
    amount_inr: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    prediction_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_income: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_subscription: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    anomaly_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    recurrence: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    overrides: Mapped[list["CategoryOverride"]] = relationship(back_populates="transaction")


class CategoryOverride(Base):
    __tablename__ = "category_overrides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), nullable=False, index=True)
    previous_category: Mapped[str] = mapped_column(String(100), nullable=False)
    new_category: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False, default="manual_override")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    transaction: Mapped[Transaction] = relationship(back_populates="overrides")


class UserFeedback(Base):
    __tablename__ = "user_feedback"
    __table_args__ = (
        Index("ix_user_feedback_created_at", "created_at"),
        Index("ix_user_feedback_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True, default=1)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), nullable=True, index=True)
    transaction_text: Mapped[str] = mapped_column(String(300), nullable=False)
    predicted_category: Mapped[str] = mapped_column(String(100), nullable=False)
    corrected_category: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class BudgetRecommendation(Base):
    __tablename__ = "budget_recommendations"
    __table_args__ = (UniqueConstraint("month", "category", name="uq_budget_month_category"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    current_spend: Mapped[float] = mapped_column(Float, nullable=False)
    recommended_budget: Mapped[float] = mapped_column(Float, nullable=False)
    potential_savings: Mapped[float] = mapped_column(Float, nullable=False)
    advice: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class MonthlySummary(Base):
    __tablename__ = "monthly_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    month: Mapped[str] = mapped_column(String(7), nullable=False, unique=True, index=True)
    total_income: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_expense: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    net_savings: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    health_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ai_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint("user_id", "category", "month", "year", name="uq_budget_user_category_month_year"),
        Index("ix_budgets_user_month_year", "user_id", "month", "year"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    monthly_limit: Mapped[float] = mapped_column(Float, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class SavingsGoal(Base):
    __tablename__ = "savings_goals"
    __table_args__ = (Index("ix_savings_goals_user_target_date", "user_id", "target_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    target_amount: Mapped[float] = mapped_column(Float, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    current_saved: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_read_created", "user_id", "is_read", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class WishlistItem(Base):
    __tablename__ = "wishlist_items"
    __table_args__ = (Index("ix_wishlist_items_user_priority", "user_id", "priority", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    target_amount: Mapped[float] = mapped_column(Float, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    notes: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class InstantSavingsEntry(Base):
    __tablename__ = "instant_savings_entries"
    __table_args__ = (
        Index("ix_instant_savings_entries_user_created", "user_id", "created_at"),
        Index("ix_instant_savings_entries_user_wishlist_created", "user_id", "wishlist_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    wishlist_id: Mapped[int] = mapped_column(Integer, ForeignKey("wishlist_items.id"), nullable=True, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    note: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
