import os
from typing import Optional


def _env(name: str, default: str = "") -> str:
    """
    Read environment variable safely.
    Never hardcode secrets in git history.
    """
    return os.getenv(name, default).strip()


class Settings:
    # Stripe (NO defaults for secrets)
    STRIPE_SECRET_KEY: str = _env("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLIC_KEY: str = _env("STRIPE_PUBLIC_KEY", "")

    # Optional: webhook signing secret (recommended)
    STRIPE_WEBHOOK_SECRET: str = _env("STRIPE_WEBHOOK_SECRET", "")

    # Database
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

    # App
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    ADMIN_API_KEY: str = _env("ADMIN_API_KEY", "")


settings = Settings()
