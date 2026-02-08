from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    # Database - Use the enterprise database where your data is
    DATABASE_URL: str = "postgresql://pie:piepass@127.0.0.1:55432/pie_enterprise"
    ENTERPRISE_ADMIN_KEY: str = "test_admin_key_123"
    
    # Stripe
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_...")
    
    # Redis for queue
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # App settings
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
