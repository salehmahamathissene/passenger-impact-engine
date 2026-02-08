from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

# Import your ACTUAL working models
try:
    from pie.pro.enterprise_models import Base
    print("✅ Using pie.pro.enterprise_models.Base")
    target_metadata = Base.metadata
except ImportError as e:
    print(f"❌ Could not import enterprise models: {e}")
    # Fallback to empty metadata
    from sqlalchemy.orm import DeclarativeBase
    class Base(DeclarativeBase):
        pass
    target_metadata = Base.metadata

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    if not url:
        print("❌ No DATABASE_URL found")
        return
    url = url.replace("+psycopg2", "")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    if not url:
        print("❌ No DATABASE_URL found")
        return
    url = url.replace("+psycopg2", "")
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
