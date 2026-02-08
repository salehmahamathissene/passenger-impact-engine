import os
import sys
sys.path.append('src')

from dotenv import load_dotenv
load_dotenv('.env.working')

print("🏗️  CREATING ENTERPRISE DATABASE TABLES")
print("=" * 50)

DATABASE_URL = os.environ.get('DATABASE_URL')
print(f"Database URL: {DATABASE_URL}")

try:
    from pie.pro.db import Base, engine
    
    print("\n🔗 Testing database connection...")
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"✅ Connected to: {version}")
        
        # Check existing tables
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        existing_tables = [row[0] for row in result]
        print(f"📊 Existing tables: {len(existing_tables)}")
        for table in existing_tables:
            print(f"  - {table}")
    
    print("\n📈 Creating enterprise tables...")
    
    # Import all models to register them
    from pie.pro import models
    from pie.pro import enterprise_models
    
    # Create only enterprise tables
    print("Creating enterprise_companies table...")
    enterprise_models.EnterpriseCompany.__table__.create(bind=engine, checkfirst=True)
    
    print("Creating enterprise_invoices table...")
    enterprise_models.EnterpriseInvoice.__table__.create(bind=engine, checkfirst=True)
    
    print("Creating enterprise_orders table...")
    enterprise_models.EnterpriseOrder.__table__.create(bind=engine, checkfirst=True)
    
    print("Creating enterprise_contracts table...")
    enterprise_models.EnterpriseContract.__table__.create(bind=engine, checkfirst=True)
    
    print("Creating enterprise_jobs table...")
    enterprise_models.EnterpriseJob.__table__.create(bind=engine, checkfirst=True)
    
    print("\n✅ Enterprise tables created/verified")
    
    # Verify
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'enterprise%'
            ORDER BY table_name
        """))
        enterprise_tables = [row[0] for row in result]
        
        print(f"\n🏢 Enterprise tables in database ({len(enterprise_tables)}):")
        for table in enterprise_tables:
            print(f"  ✅ {table}")
            
            # Show column count
            col_result = conn.execute(text(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = '{table}'
            """))
            col_count = col_result.scalar()
            print(f"     Columns: {col_count}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
