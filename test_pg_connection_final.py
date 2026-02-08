import os
import sys
sys.path.append('src')

from dotenv import load_dotenv
load_dotenv('.env.working')

print("🔌 TESTING POSTGRESQL CONNECTION FINAL")
print("=" * 50)

DATABASE_URL = os.environ.get('DATABASE_URL', '')
print(f"Database URL: {DATABASE_URL}")

# Import and test
try:
    from pie.pro.db import engine, test_connection, Base
    
    print("\nTesting connection...")
    if test_connection():
        # Create tables if they don't exist
        print("\n📊 Creating/verifying tables...")
        
        # Import models to ensure they're registered with Base
        from pie.pro import enterprise_models
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created/verified")
        
        # List tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📋 Tables in database ({len(tables)}):")
        for table in sorted(tables):
            print(f"  - {table}")
            
            # Show column info for enterprise tables
            if 'enterprise' in table:
                try:
                    columns = inspector.get_columns(table)
                    print(f"    Columns:")
                    for col in columns[:3]:  # First 3 columns
                        print(f"      {col['name']} ({str(col['type'])})")
                    if len(columns) > 3:
                        print(f"      ... and {len(columns)-3} more")
                except:
                    pass
    
    else:
        print("❌ Connection test failed")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
