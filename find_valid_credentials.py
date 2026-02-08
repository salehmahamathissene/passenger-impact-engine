import os
import sys
from pathlib import Path

# Check for common database files
db_files = [
    "passenger_impact.db",
    "test.db", 
    "development.db",
    "database.db",
    "app.db",
    "data/database.sqlite3",
    "instance/app.db"
]

print("🔍 Looking for database files...")
found = False
for db_file in db_files:
    path = Path(db_file)
    if path.exists():
        print(f"✅ Found database: {db_file}")
        print(f"   Size: {path.stat().st_size:,} bytes")
        found = True
        
        # Try to read it
        try:
            import sqlite3
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # List tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"   Tables: {', '.join([t[0] for t in tables])}")
            
            # Look for company/API key tables
            company_tables = [t[0] for t in tables if 'company' in t[0].lower()]
            api_key_tables = [t[0] for t in tables if 'api' in t[0].lower() or 'key' in t[0].lower()]
            
            if company_tables:
                print(f"\n📋 Companies:")
                for table in company_tables[:2]:
                    cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                    rows = cursor.fetchall()
                    if rows:
                        print(f"   {table}:")
                        for row in rows:
                            print(f"     {row}")
            
            if api_key_tables:
                print(f"\n🔑 API Keys:")
                for table in api_key_tables[:2]:
                    cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                    rows = cursor.fetchall()
                    if rows:
                        print(f"   {table}:")
                        for row in rows:
                            print(f"     {row}")
            
            conn.close()
        except Exception as e:
            print(f"   Error reading: {e}")
        
        print("-" * 50)

if not found:
    print("❌ No database files found in common locations")
    
print("\n📋 To manually check:")
print("1. Look for .env files: find . -name '*.env' -o -name '.env*'")
print("2. Check for DATABASE_URL in environment: echo \$DATABASE_URL")
print("3. Check application config files")
