import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

print("🚀 SETTING UP PRODUCTION POSTGRESQL DATABASE")
print("=" * 50)

# Read environment
from dotenv import load_dotenv
load_dotenv('.env.working')

DATABASE_URL = os.environ.get('DATABASE_URL', '')
print(f"Database URL from env: {DATABASE_URL}")

if not DATABASE_URL:
    print("❌ DATABASE_URL not set!")
    sys.exit(1)

# Parse database URL
# Format: postgresql://user:password@host:port/database
if DATABASE_URL.startswith('postgresql://'):
    # Simple parsing for local development
    db_parts = DATABASE_URL.replace('postgresql://', '').split('/')
    db_name = db_parts[1] if len(db_parts) > 1 else 'passenger_impact_prod'
    credentials_host = db_parts[0].split('@')
    
    if len(credentials_host) > 1:
        user_pass = credentials_host[0].split(':')
        db_user = user_pass[0]
        db_password = user_pass[1] if len(user_pass) > 1 else ''
        db_host_port = credentials_host[1].split(':')
        db_host = db_host_port[0]
        db_port = db_host_port[1] if len(db_host_port) > 1 else '5432'
    else:
        # No credentials in URL (common for local)
        db_user = os.environ.get('USER', 'postgres')
        db_password = ''
        db_host_port = credentials_host[0].split(':')
        db_host = db_host_port[0]
        db_port = db_host_port[1] if len(db_host_port) > 1 else '5432'
    
    print(f"Database: {db_name}")
    print(f"User: {db_user}")
    print(f"Host: {db_host}:{db_port}")
    
    # Test connection
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        print("✅ PostgreSQL connection successful!")
        
        # Create tables if they don't exist
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        
        print(f"\n📊 Existing tables: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTry creating the database manually:")
        print(f"  createdb {db_name}")
        print(f"  Or connect as postgres user: sudo -u postgres psql")
        print(f"  Then: CREATE DATABASE {db_name};")
else:
    print(f"❌ Not a PostgreSQL URL: {DATABASE_URL}")
