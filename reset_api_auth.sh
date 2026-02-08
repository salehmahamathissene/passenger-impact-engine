#!/bin/bash
echo "🔄 RESETTING API AUTHENTICATION"
echo "================================"

source .env.working

# Generate a new secure API key
NEW_API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "New API Key: $NEW_API_KEY"

# Update .env.working
sed -i "s/API_SECRET=.*/API_SECRET='$NEW_API_KEY'/" .env.working
echo "✅ Updated .env.working"

# Now update the database with proper hash
python3 <<'PY'
import os
import argon2
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv('.env.working')

DATABASE_URL = os.environ.get('DATABASE_URL')
COMPANY_ID = os.environ.get('COMPANY_ID')
API_KEY = os.environ.get('API_SECRET')

print(f"Company ID: {COMPANY_ID}")
print(f"API Key to hash: {API_KEY[:10]}...")

# Create hash using Argon2
hasher = argon2.PasswordHasher()
api_hash = hasher.hash(API_KEY)
print(f"Argon2 Hash: {api_hash[:50]}...")

# Update database
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute(
        text('UPDATE enterprise_companies SET api_key_hash = :hash WHERE id = :id'),
        {'hash': api_hash, 'id': COMPANY_ID}
    )
    conn.commit()
    
    print(f"✅ Updated database: {result.rowcount} row(s) affected")
    
    # Verify
    company = conn.execute(
        text('SELECT legal_name, api_key_hash FROM enterprise_companies WHERE id = :id'),
        {'id': COMPANY_ID}
    ).fetchone()
    
    if company:
        print(f"✅ Verification: {company[0]}")
        print(f"   Hash in DB: {company[1][:50]}...")
        
        # Test verification
        try:
            hasher.verify(company[1], API_KEY)
            print("   ✅ Hash verification successful")
        except:
            print("   ❌ Hash verification failed")
PY

# Reload environment
source .env.working

# Test authentication
echo ""
echo "🔐 TESTING NEW AUTHENTICATION"
echo "=============================="

curl -s -H "X-Company-Id: $COMPANY_ID" -H "X-Api-Key: $API_SECRET" \
  http://127.0.0.1:8080/enterprise/invoices | python3 -m json.tool
