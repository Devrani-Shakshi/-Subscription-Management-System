"""
Application configuration via Pydantic Settings.
All secrets and URLs loaded from environment variables.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Global application settings — immutable after startup."""

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "SubManager"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/submanager"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # ── Redis ────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT / Auth ───────────────────────────────────────────────
    JWT_SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Idle timeouts (seconds)
    IDLE_TIMEOUT_SUPER_ADMIN: int = 1800   # 30 min
    IDLE_TIMEOUT_COMPANY: int = 1800       # 30 min
    IDLE_TIMEOUT_PORTAL_USER: int = 3600   # 60 min

    # Absolute session limits (seconds)
    ABS_TIMEOUT_ADMIN: int = 28800         # 8 h
    ABS_TIMEOUT_PORTAL: int = 2592000      # 30 days

    # ── Rate limiting ────────────────────────────────────────────
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_SECONDS: int = 900       # 15 min

    # ── Sentry (error tracking) ──────────────────────────────────
    SENTRY_DSN: str = ""

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
