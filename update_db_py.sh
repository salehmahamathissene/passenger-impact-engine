#!/bin/bash
echo "🔄 UPDATING DB.PY FOR POSTGRESQL"
echo "================================"

DB_FILE="src/pie/pro/db.py"

if [ -f "$DB_FILE" ]; then
    echo "Current db.py:"
    echo "=============="
    cat "$DB_FILE"
    
    echo ""
    echo "Updating db.py for PostgreSQL..."
    
    cat > "$DB_FILE" <<'PYEOF'
"""
Database configuration for PostgreSQL
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Get database URL from environment with fallback
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    # Default to SQLite for development, but warn
    import warnings
    warnings.warn("DATABASE_URL not set, falling back to SQLite (NOT FOR PRODUCTION!)")
    DATABASE_URL = "sqlite:///./pie.db"

# Check if using PostgreSQL
USING_POSTGRES = "postgresql://" in DATABASE_URL

# Engine configuration
engine_kwargs = {}
if USING_POSTGRES:
    # PostgreSQL-specific optimizations
    engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 0,
        "pool_pre_ping": True,
        "echo": False,  # Set to True for SQL query logging
        "connect_args": {
            "connect_timeout": 10,
            "application_name": "passenger_impact"
        }
    })
else:
    # SQLite configuration (development only)
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
        "echo": False
    })

engine = create_engine(DATABASE_URL, **engine_kwargs)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test connection
def test_connection():
    try:
        with engine.connect() as conn:
            if USING_POSTGRES:
                result = conn.execute("SELECT version()")
                version = result.scalar()
                print(f"✅ PostgreSQL connected: {version}")
            else:
                print("✅ SQLite connected (development mode)")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
PYEOF
    
    echo "✅ db.py updated for PostgreSQL!"
else
    echo "❌ db.py not found, creating it..."
    mkdir -p src/pie/pro
    # Run the same creation as above
    ./update_db_py.sh
fi
