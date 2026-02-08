import os
import sys
import uuid
import hashlib
from datetime import datetime
sys.path.append('src')

from dotenv import load_dotenv
load_dotenv('.env.working')

from sqlalchemy import create_engine, text

print("👔 CREATING ENTERPRISE COMPANY")
print("=" * 40)

DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)

# Get environment variables
company_id_str = os.environ.get('COMPANY_ID')
api_key = os.environ.get('API_KEY')

if not company_id_str or not api_key:
    print("❌ COMPANY_ID or API_KEY not set in environment")
    print(f"   COMPANY_ID: {company_id_str}")
    print(f"   API_KEY: {'*' * len(api_key) if api_key else 'NOT SET'}")
    sys.exit(1)

try:
    company_id = uuid.UUID(company_id_str)
except ValueError:
    print(f"❌ Invalid COMPANY_ID format: {company_id_str}")
    sys.exit(1)

print(f"Company ID: {company_id}")
print(f"API Key: {'*' * len(api_key)}")

# Hash the API key (SHA-256)
api_key_hash = hashlib.sha256(api_key.encode('utf-8')).hexdigest()
print(f"API Key Hash: {api_key_hash[:16]}...")

with engine.connect() as conn:
    # Check if company exists
    result = conn.execute(
        text('SELECT id, legal_name, api_key_hash FROM enterprise_companies WHERE id = :id'),
        {'id': str(company_id)}
    ).fetchone()
    
    if result:
        print(f"\n✅ Company already exists:")
        print(f"   ID: {result[0]}")
        print(f"   Name: {result[1]}")
        print(f"   Existing API Key Hash: {result[2][:16]}...")
        
        # Check if API key matches
        if result[2] == api_key_hash:
            print("   ✅ API key matches")
        else:
            print("   ⚠️  API key does NOT match stored hash")
            print("   Updating API key hash...")
            conn.execute(
                text('UPDATE enterprise_companies SET api_key_hash = :hash WHERE id = :id'),
                {'hash': api_key_hash, 'id': str(company_id)}
            )
            conn.commit()
            print("   ✅ API key hash updated")
    else:
        print("\n📝 Creating new enterprise company...")
        
        # Insert company
        conn.execute(
            text('''
                INSERT INTO enterprise_companies (
                    id, legal_name, trading_name, tier, industry, 
                    country, support_email, api_key_hash,
                    is_active, plan,
                    stripe_customer_id, stripe_subscription_id, current_period_end,
                    created_at, updated_at
                ) VALUES (
                    :id, :legal_name, :trading_name, :tier, :industry,
                    :country, :support_email, :api_key_hash,
                    :is_active, :plan,
                    :stripe_customer_id, :stripe_subscription_id, :current_period_end,
                    NOW(), NOW()
                )
            '''),
            {
                'id': str(company_id),
                'legal_name': 'Passenger Impact Engine Enterprise',
                'trading_name': 'PIE Enterprise',
                'tier': 'small',
                'industry': 'airline',
                'country': 'US',
                'support_email': 'enterprise@pie.example.com',
                'api_key_hash': api_key_hash,
                'is_active': True,
                'plan': 'free',
                'stripe_customer_id': None,
                'stripe_subscription_id': None,
                'current_period_end': None
            }
        )
        conn.commit()
        print("✅ Enterprise company created successfully!")
    
    # Verify
    result = conn.execute(
        text('''
            SELECT 
                id, legal_name, plan, is_active, 
                stripe_customer_id, created_at
            FROM enterprise_companies 
            WHERE id = :id
        '''),
        {'id': str(company_id)}
    ).fetchone()
    
    print(f"\n📋 Company Details:")
    print(f"   ID: {result[0]}")
    print(f"   Name: {result[1]}")
    print(f"   Plan: {result[2]}")
    print(f"   Active: {result[3]}")
    print(f"   Stripe Customer ID: {result[4]}")
    print(f"   Created: {result[5]}")
    
    # Count total companies
    count_result = conn.execute(text('SELECT COUNT(*) FROM enterprise_companies'))
    total = count_result.scalar()
    print(f"\n📊 Total companies in database: {total}")
