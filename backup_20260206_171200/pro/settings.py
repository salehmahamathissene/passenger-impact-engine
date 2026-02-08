from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database - PRODUCTION PostgreSQL
    DATABASE_URL: str = "postgresql+psycopg://pie:pie123@localhost:5432/pie"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Stripe (enabled only if you put real keys)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_SUCCESS_URL: str = "http://localhost:8080/success?order_id={ORDER_ID}"
    STRIPE_CANCEL_URL: str = "http://localhost:8080/cancel?order_id={ORDER_ID}"

    # Enterprise auth (MUST be set in .env)
    ENTERPRISE_API_KEY: str = ""

    # Pricing (in cents)
    CURRENCY: str = "eur"
    STARTER_PRICE_EUR: int = 9900
    PRO_PRICE_EUR: int = 49900
    ENTERPRISE_PRICE_EUR: int = 199900

    # Artifacts
    ARTIFACT_ROOT: str = "artifacts"

    # SSL for production DB
    DB_SSL_MODE: Optional[str] = None


settings = Settings()
