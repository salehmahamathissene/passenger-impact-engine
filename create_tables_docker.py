import os
import sys
sys.path.append('src')

from dotenv import load_dotenv
load_dotenv('.env.working')

print("🐳 CREATING TABLES IN DOCKER POSTGRESQL")
print("=" * 50)

DATABASE_URL = os.environ.get('DATABASE_URL', '')
print(f"Using DATABASE_URL: {DATABASE_URL}")

try:
    from pie.pro.db import init_db, engine, Base
    
    print("\n🔗 Testing connection...")
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"✅ Connected to: {version}")
    
    print("\n📊 Creating tables...")
    
    # Import models to register them
    print("Importing models...")
    from pie.pro import models
    from pie.pro import enterprise_models
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created!")
    
    # List tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\n📋 Created {len(tables)} tables:")
    enterprise_tables = [t for t in tables if 'enterprise' in t]
    other_tables = [t for t in tables if 'enterprise' not in t]
    
    if enterprise_tables:
        print("\n🏢 Enterprise tables:")
        for table in sorted(enterprise_tables):
            print(f"  - {table}")
    
    if other_tables:
        print("\n📁 Other tables:")
        for table in sorted(other_tables):
            print(f"  - {table}")
            
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
