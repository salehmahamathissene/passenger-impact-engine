import os
import sys
sys.path.append(os.getcwd() + '/src')

from dotenv import load_dotenv
load_dotenv('.env.working')

from sqlalchemy import create_engine, text, inspect
from pie.pro.database import Base
from pie.pro import enterprise_models

DATABASE_URL = os.environ.get('DATABASE_URL')
print(f"🚀 Using database: {DATABASE_URL}")

if 'sqlite' in DATABASE_URL:
    print("❌ ERROR: Still using SQLite! Aborting.")
    print("Change DATABASE_URL in .env.working to PostgreSQL")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

# Test connection
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)

# Create tables
print("\n📊 Creating enterprise tables...")
Base.metadata.create_all(bind=engine)
print("✅ Tables created successfully!")

# Verify tables were created
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"\n📋 Tables in database ({len(tables)} total):")
for table in sorted(tables):
    print(f"  - {table}")
    # Show columns for enterprise tables
    if 'enterprise' in table:
        columns = inspector.get_columns(table)
        for col in columns:
            print(f"    └─ {col['name']} ({col['type']})")
