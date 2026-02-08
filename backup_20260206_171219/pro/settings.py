from __future__ import annotations

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    DATABASE_URL: str = "postgresql+psycopg://pie:pie123@localhost:5432/pie"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Stripe (optional; only works if real keys are set)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_SUCCESS_URL: str = "http://localhost:8080/success?order_id={ORDER_ID}"
    STRIPE_CANCEL_URL: str = "http://localhost:8080/cancel?order_id={ORDER_ID}"

    # Enterprise (required in real enterprise environments)
    ENTERPRISE_ADMIN_KEY: str = ""  # required for invoice settlement

    # Pricing (cents)
    CURRENCY: str = "eur"
    STARTER_PRICE_EUR: int = 9900
    PRO_PRICE_EUR: int = 49900
    ENTERPRISE_PRICE_EUR: int = 199900

    # Artifacts
    ARTIFACT_ROOT: str = "artifacts"


settings = Settings()
