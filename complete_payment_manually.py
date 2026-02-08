import os
import sys
import uuid
import stripe
from datetime import datetime, timedelta
sys.path.append('src')

from dotenv import load_dotenv
load_dotenv('.env.working')

print("💰 COMPLETE PAYMENT FLOW MANUALLY")
print("=" * 50)

# Initialize Stripe
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

print("\n1️⃣ Creating Stripe subscription...")
try:
    # Create subscription for the customer
    subscription = stripe.Subscription.create(
        customer=customer_id,
        items=[{
            "price": stripe_price,
        }],
        payment_behavior="default_incomplete",
        expand=["latest_invoice.payment_intent"],
        metadata={
            "company_id": company_id,
            "created_by": "manual_test"
        }
    )
    
    print(f"✅ Subscription created: {subscription.id}")
    print(f"   Status: {subscription.status}")
    print(f"   Current period end: {datetime.fromtimestamp(subscription.current_period_end).isoformat()}")
    
    # Mark subscription as active by paying the invoice
    print("\n2️⃣ Paying invoice...")
    invoice = stripe.Invoice.retrieve(subscription.latest_invoice)
    
    # Pay invoice with test payment method
    paid_invoice = stripe.Invoice.pay(
        invoice.id,
        paid_out_of_band=True  # Mark as paid without actual payment
    )
    
    print(f"✅ Invoice paid: {paid_invoice.id}")
    print(f"   Status: {paid_invoice.status}")
    
    # Update subscription status
    updated_subscription = stripe.Subscription.retrieve(subscription.id)
    print(f"\n3️⃣ Subscription status updated: {updated_subscription.status}")
    
    print("\n4️⃣ Updating database...")
    # Update company in database
    with engine.connect() as conn:
        conn.execute(
            text('''
                UPDATE enterprise_companies 
                SET plan = 'pro',
                    is_active = true,
                    stripe_subscription_id = :subscription_id,
                    current_period_end = TO_TIMESTAMP(:period_end),
                    updated_at = NOW()
                WHERE id = :company_id
            '''),
            {
                'company_id': company_id,
                'subscription_id': subscription.id,
                'period_end': subscription.current_period_end
            }
        )
        conn.commit()
    
    print("✅ Database updated!")
    
    # Verify update
    with engine.connect() as conn:
        result = conn.execute(
            text('SELECT plan, is_active, stripe_subscription_id FROM enterprise_companies WHERE id = :id'),
            {'id': company_id}
        ).fetchone()
        
        print(f"\n📊 Database verification:")
        print(f"   Plan: {result[0]}")
        print(f"   Active: {result[1]}")
        print(f"   Subscription ID: {result[2]}")
    
    print("\n" + "=" * 50)
    print("🎉 PAYMENT FLOW COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    print("\nCompany now has active PRO subscription!")
    
except stripe.error.StripeError as e:
    print(f"❌ Stripe error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
