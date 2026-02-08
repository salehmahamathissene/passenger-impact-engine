"""
FIX API AUTHENTICATION FOR REAL - NOT FAKE
"""
import os
import secrets
import argon2
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv('.env.working')

print("🔧 FIXING API AUTHENTICATION")
print("=" * 50)

# Generate a real API key
NEW_API_KEY = secrets.token_urlsafe(32)
print(f"Generated API Key: {NEW_API_KEY}")

# Update .env.working file
env_file = '.env.working'
with open(env_file, 'r') as f:
    content = f.read()

# Replace API_SECRET line
if 'API_SECRET=' in content:
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if line.startswith('API_SECRET='):
            new_lines.append(f"API_SECRET='{NEW_API_KEY}'")
        else:
            new_lines.append(line)
    
    with open(env_file, 'w') as f:
        f.write('\n'.join(new_lines))
    print(f"✅ Updated {env_file}")
else:
    print(f"❌ API_SECRET not found in {env_file}")

# Now update the database
DATABASE_URL = os.environ.get('DATABASE_URL')
COMPANY_ID = os.environ.get('COMPANY_ID')

if DATABASE_URL and COMPANY_ID:
    print(f"\n📊 Updating database for company: {COMPANY_ID}")
    
    # Hash the API key with Argon2
    hasher = argon2.PasswordHasher()
    api_hash = hasher.hash(NEW_API_KEY)
    print(f"API Hash (first 50 chars): {api_hash[:50]}...")
    
    # Update database
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # Update the API key hash
        result = conn.execute(
            text('UPDATE enterprise_companies SET api_key_hash = :hash WHERE id = :id'),
            {'hash': api_hash, 'id': COMPANY_ID}
        )
        conn.commit()
        print(f"✅ Database updated: {result.rowcount} row(s) affected")
        
        # Verify
        company = conn.execute(
            text('SELECT legal_name, api_key_hash FROM enterprise_companies WHERE id = :id'),
            {'id': COMPANY_ID}
        ).fetchone()
        
        if company:
            print(f"✅ Company: {company[0]}")
            print(f"✅ Hash stored: {company[1][:50]}...")
            
            # Test verification
            try:
                hasher.verify(company[1], NEW_API_KEY)
                print("✅ Hash verification successful")
            except Exception as e:
                print(f"❌ Hash verification failed: {e}")
else:
    print("❌ Missing DATABASE_URL or COMPANY_ID")

print("\n🎯 RELOAD ENVIRONMENT AND TEST:")
print(f"  source .env.working")
print(f"  curl -H 'X-Company-Id: {COMPANY_ID}' -H 'X-Api-Key: {NEW_API_KEY}' http://127.0.0.1:8080/enterprise/billing/subscription")
