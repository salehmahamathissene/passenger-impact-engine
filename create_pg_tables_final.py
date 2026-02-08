import os
import sys
sys.path.append('src')

from dotenv import load_dotenv
load_dotenv('.env.working')

print("🚀 CREATING POSTGRESQL TABLES")
print("=" * 50)

DATABASE_URL = os.environ.get('DATABASE_URL')
print(f"Using database: {DATABASE_URL}")

try:
    from pie.pro.database import Base, engine
    from pie.pro import enterprise_models
    
    print("\n📊 Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")
    
    # Verify
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\n📋 Tables created ({len(tables)}):")
    for table in sorted(tables):
        print(f"  - {table}")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nTrying alternative import...")
    try:
        # Try creating engine directly
        from sqlalchemy import create_engine, text
        
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Test connection
            conn.execute(text("SELECT 1"))
            print("✅ Database connection works")
            
            # Check existing tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = result.fetchall()
            print(f"\n📊 Existing tables: {len(tables)}")
            for table in tables:
                print(f"  - {table[0]}")
                
    except Exception as e2:
        print(f"❌ Failed: {e2}")
