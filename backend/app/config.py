from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI-Based Expense Categorization"
    api_prefix: str = "/api"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/smart_budget_db"
    cors_origins: str = "http://localhost:5173"
    cors_origin_regex: str = r"https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    model_path: str = "app/ml/ml_model.pkl"
    auth_required: bool = True
    jwt_secret_key: str = "dev-insecure-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    default_user_id: int = 1
    ai_rate_limit_per_minute: int = 30
    email_notifications_enabled: bool = False
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str = "Smart Budget Planner"
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()
