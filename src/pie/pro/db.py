"""
Database configuration for Pro/Enterprise module.
This file MUST expose: Base, engine, SessionLocal, get_db
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .settings import get_settings

settings = get_settings()

# Base declarative class (imported by models)
Base = declarative_base()

# SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
