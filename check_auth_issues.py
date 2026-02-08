"""
REAL authentication check - not fake examples
"""
import os
import sys
import hashlib
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv('.env.working')

DATABASE_URL = os.environ.get('DATABASE_URL')
API_KEY = os.environ.get('API_SECRET')
COMPANY_ID = os.environ.get('COMPANY_ID')

print("🔍 REAL AUTHENTICATION DEBUG")
print("=" * 50)

print(f"Company ID from env: {COMPANY_ID}")
print(f"API Key length: {len(API_KEY) if API_KEY else 0}")

if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # Check if company exists
        company = conn.execute(
            text('SELECT id, legal_name, api_key_hash FROM enterprise_companies WHERE id = :id'),
            {'id': COMPANY_ID}
        ).fetchone()
        
        if company:
            print(f"✅ Company found: {company[1]}")
            print(f"   Company ID in DB: {company[0]}")
            print(f"   API Key hash in DB: {company[2][:20] if company[2] else 'None'}")
            
            # Hash the current API key to compare
            if API_KEY:
                import argon2
                hasher = argon2.PasswordHasher()
                try:
                    # Try to verify
                    print("   Trying Argon2 verification...")
                    print("   Note: This will fail if hash was created differently")
                except:
                    print("   Argon2 verification failed - might be different algorithm")
                    
                # Simple hash for debugging
                simple_hash = hashlib.sha256(API_KEY.encode()).hexdigest()
                print(f"   SHA256 of current key: {simple_hash[:20]}...")
        else:
            print("❌ Company not found in database")
            
        # Check what's actually in the DB
        print("\n📋 All companies in database:")
        companies = conn.execute(
            text('SELECT id, legal_name, api_key_hash FROM enterprise_companies')
        ).fetchall()
        
        for c in companies:
            hash_preview = c[2][:20] + '...' if c[2] else 'None'
            print(f"   {c[0]}: {c[1]} (hash: {hash_preview})")
