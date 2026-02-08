import os
import sys
import uuid
import stripe
from datetime import datetime, timedelta
import time
sys.path.append('src')

from dotenv import load_dotenv
load_dotenv('.env.working')

print("💰 COMPLETE PAYMENT WITH NEW STRIPE API")
print("=" * 50)

# Initialize Stripe with newer API version
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
company_id = os.environ.get('COMPANY_ID')
stripe_price = os.environ.get('STRIPE_PRICE_PRO_MONTHLY')

print(f"Company ID: {company_id}")
print(f"Stripe Price: {stripe_price}")

# Get existing customer ID from database
from sqlalchemy import create_engine, text
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Get current customer ID
    result = conn.execute(
        text('SELECT legal_name, stripe_customer_id FROM enterprise_companies WHERE id = :id'),
        {'id': company_id}
    ).fetchone()
    
    if result:
        company_name = result[0]
        customer_id = result[1]
        print(f"Company: {company_name}")
        print(f"Existing Stripe Customer ID: {customer_id}")
    else:
        print("❌ Company not found in database")
        sys.exit(1)

print("\n📝 OPTION 1: Use existing checkout URL")
print("======================================")
print("The easiest way is to use the checkout URL already generated:")
print("https://checkout.stripe.com/c/pay/cs_test_b1bZn7k6oUSdn4hLFw0xMZRRIwQBHhRUOFOmxl5L5B5kgfmGgPrIbgTwx5")
print("")
print("Just open that URL in browser and use test card: 4242 4242 4242 4242")

print("\n📝 OPTION 2: Create new checkout session")
print("========================================")

try:
    # Create a new checkout session
    checkout_session = stripe.checkout.Session.create(
        customer=customer_id,
        line_items=[{
            "price": stripe_price,
            "quantity": 1
        }],
        mode="subscription",
        success_url="http://localhost:3000/billing/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="http://localhost:3000/billing/cancel",
        metadata={
            "company_id": company_id,
            "test": "manual"
        },
        subscription_data={
            "metadata": {
                "company_id": company_id,
                "created_via": "manual_api"
            }
        }
    )
    
    print(f"✅ New checkout session created:")
    print(f"   Session ID: {checkout_session.id}")
    print(f"   URL: {checkout_session.url}")
    print(f"   Customer: {checkout_session.customer}")
    
    # Save to file
    import json
    with open('/tmp/new_checkout_session.json', 'w') as f:
        json.dump({
            "session_id": checkout_session.id,
            "url": checkout_session.url,
            "customer_id": checkout_session.customer
        }, f, indent=2)
    
    print(f"\n💾 Saved to: /tmp/new_checkout_session.json")
    
except Exception as e:
    print(f"❌ Error creating checkout: {e}")

print("\n📝 OPTION 3: Direct database update (for testing)")
print("=================================================")
print("For testing, we can directly update the database to PRO plan:")
print("")

update_choice = input("Update database to PRO plan? (y/N): ").strip().lower()
if update_choice == 'y':
    with engine.connect() as conn:
        # Create mock subscription ID
        subscription_id = f'sub_mock_{int(time.time())}'
        
        # Update to PRO plan
        conn.execute(
            text('''
                UPDATE enterprise_companies 
                SET plan = 'pro',
                    is_active = true,
                    stripe_subscription_id = :subscription_id,
                    current_period_end = NOW() + INTERVAL '30 days',
                    updated_at = NOW()
                WHERE id = :company_id
            '''),
            {
                'company_id': company_id,
                'subscription_id': subscription_id
            }
        )
        conn.commit()
        
        print(f"\n✅ Updated to PRO plan!")
        print(f"   Subscription ID: {subscription_id}")
        print(f"   Plan: pro")
        print(f"   Active: true")
        print(f"   Period: 30 days")
        
        # Verify
        result = conn.execute(
            text('SELECT plan, is_active, stripe_subscription_id FROM enterprise_companies WHERE id = :id'),
            {'id': company_id}
        ).fetchone()
        
        print(f"\n📊 Verification:")
        print(f"   Plan: {result[0]}")
        print(f"   Active: {result[1]}")
        print(f"   Subscription ID: {result[2]}")
else:
    print("Skipping database update.")

print("\n" + "=" * 50)
print("🎯 NEXT STEPS:")
print("=" * 50)
print("")
print("1. FOR REAL PAYMENT TEST:")
print("   Open checkout URL in browser and use test card")
print("")
print("2. FOR DEVELOPMENT TESTING:")
print("   The database is already updated to PRO plan")
print("")
print("3. TO VERIFY:")
print("   curl -s 'http://127.0.0.1:8080/enterprise/billing/subscription' \\")
print("     -H 'X-Company-Id: $COMPANY_ID' \\")
print("     -H 'X-Api-Key: $API_KEY'")
print("")
print("4. TO SET UP WEBHOOKS (for production):")
print("   Follow instructions in setup_webhooks_guide.sh")
