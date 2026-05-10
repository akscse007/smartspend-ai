CREATE DATABASE smart_budget_db;

\c smart_budget_db;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    date DATE NOT NULL,
    description VARCHAR(300) NOT NULL,
    clean_description VARCHAR(300) NOT NULL,
    merchant VARCHAR(150) NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'INR',
    amount_inr DOUBLE PRECISION NOT NULL,
    category VARCHAR(100) NOT NULL,
    prediction_confidence DOUBLE PRECISION NOT NULL DEFAULT 0,
    is_income BOOLEAN NOT NULL DEFAULT FALSE,
    is_subscription BOOLEAN NOT NULL DEFAULT FALSE,
    anomaly_flag BOOLEAN NOT NULL DEFAULT FALSE,
    recurrence VARCHAR(20) NOT NULL DEFAULT 'none',
    source_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE transactions DROP CONSTRAINT IF EXISTS transactions_source_hash_key;
ALTER TABLE transactions ADD CONSTRAINT uq_transactions_user_source_hash UNIQUE(user_id, source_hash);

CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, date);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_transactions_merchant ON transactions(merchant);
CREATE INDEX IF NOT EXISTS idx_transactions_anomaly_flag ON transactions(anomaly_flag);
CREATE INDEX IF NOT EXISTS idx_transactions_date_is_income ON transactions(date, is_income);
CREATE INDEX IF NOT EXISTS idx_transactions_category_date ON transactions(category, date);

CREATE TABLE IF NOT EXISTS category_overrides (
    id SERIAL PRIMARY KEY,
    transaction_id INTEGER NOT NULL REFERENCES transactions(id),
    previous_category VARCHAR(100) NOT NULL,
    new_category VARCHAR(100) NOT NULL,
    reason VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    transaction_id INTEGER NULL REFERENCES transactions(id),
    transaction_text VARCHAR(300) NOT NULL,
    predicted_category VARCHAR(100) NOT NULL,
    corrected_category VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_feedback_user_id ON user_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_user_feedback_created_at ON user_feedback(created_at);

CREATE TABLE IF NOT EXISTS budget_recommendations (
    id SERIAL PRIMARY KEY,
    month VARCHAR(7) NOT NULL,
    category VARCHAR(100) NOT NULL,
    current_spend DOUBLE PRECISION NOT NULL,
    recommended_budget DOUBLE PRECISION NOT NULL,
    potential_savings DOUBLE PRECISION NOT NULL,
    advice TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_budget_month_category UNIQUE(month, category)
);

CREATE TABLE IF NOT EXISTS monthly_summaries (
    id SERIAL PRIMARY KEY,
    month VARCHAR(7) NOT NULL UNIQUE,
    total_income DOUBLE PRECISION NOT NULL,
    total_expense DOUBLE PRECISION NOT NULL,
    net_savings DOUBLE PRECISION NOT NULL,
    health_score DOUBLE PRECISION NOT NULL,
    ai_summary TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS budgets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    category_id INTEGER NULL,
    category VARCHAR(100) NOT NULL,
    monthly_limit DOUBLE PRECISION NOT NULL,
    month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    year INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_budget_user_category_month_year UNIQUE(user_id, category, month, year)
);

CREATE INDEX IF NOT EXISTS idx_budgets_user_id ON budgets(user_id);
CREATE INDEX IF NOT EXISTS idx_budgets_category_id ON budgets(category_id);
CREATE INDEX IF NOT EXISTS idx_budgets_category ON budgets(category);
CREATE INDEX IF NOT EXISTS idx_budgets_user_month_year ON budgets(user_id, month, year);

CREATE TABLE IF NOT EXISTS savings_goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    target_amount DOUBLE PRECISION NOT NULL,
    target_date DATE NOT NULL,
    current_saved DOUBLE PRECISION NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_savings_goals_user_id ON savings_goals(user_id);
CREATE INDEX IF NOT EXISTS idx_savings_goals_user_target_date ON savings_goals(user_id, target_date);

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_notifications_user_read_created ON notifications(user_id, is_read, created_at);
