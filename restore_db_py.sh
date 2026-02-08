#!/bin/bash
echo "🔧 RESTORING CORRECT db.py WITH init_db"
echo "========================================"

cat > src/pie/pro/db.py <<'PYEOF'
from __future__ import annotations

from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker, DeclarativeBase

import os

# Get DATABASE_URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

print(f"🔗 Connecting to database: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")

class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    poolclass=pool.QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Initialize database - create all tables"""
    print("📊 Creating database tables...")
    # Import models to register them with Base
    from . import models  # noqa: F401
    from . import enterprise_models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
PYEOF

echo "✅ db.py restored with init_db function"
python -c "from src.pie.pro.db import init_db; print('✅ init_db import test successful')" || echo "❌ init_db import failed"
