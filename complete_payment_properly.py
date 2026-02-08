import os
import sys
import uuid
import stripe
from datetime import datetime, timedelta
import time
sys.path.append('src')

from dotenv import load_dotenv
load_dotenv('.env.working')

print("💰 COMPLETE PAYMENT FLOW PROPERLY")
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

print("\n1️⃣ Creating payment method for customer...")
try:
    # Create a test payment method
    payment_method = stripe.PaymentMethod.create(
        type="card",
        card={
            "number": "4242424242424242",
            "exp_month": 12,
            "exp_year": 2034,
            "cvc": "123",
        },
    )
    print(f"✅ Test payment method created: {payment_method.id}")
    
    # Attach payment method to customer
    stripe.PaymentMethod.attach(
        payment_method.id,
        customer=customer_id,
    )
    print(f"✅ Payment method attached to customer")
    
    # Set as default payment method
    stripe.Customer.modify(
        customer_id,
        invoice_settings={
            "default_payment_method": payment_method.id,
        },
    )
    print(f"✅ Set as default payment method")
    
except Exception as e:
    print(f"⚠️  Could not create payment method: {e}")
    print("Proceeding with subscription creation...")

print("\n2️⃣ Creating Stripe subscription with immediate collection...")
try:
    # Create subscription with immediate payment attempt
    subscription = stripe.Subscription.create(
        customer=customer_id,
        items=[{
            "price": stripe_price,
        }],
        payment_behavior="default_incomplete",
        payment_settings={"save_default_payment_method": "on_subscription"},
        expand=["latest_invoice.payment_intent"],
        metadata={
            "company_id": company_id,
            "created_by": "manual_payment",
            "timestamp": str(int(time.time()))
        }
    )
    
    print(f"✅ Subscription created: {subscription.id}")
    print(f"   Status: {subscription.status}")
    
    # Get the invoice
    invoice = subscription.latest_invoice
    print(f"   Invoice: {invoice.id}")
    print(f"   Invoice status: {invoice.status}")
    
    # Check if there's a payment intent
    if invoice.payment_intent:
        payment_intent = invoice.payment_intent
        print(f"   Payment Intent: {payment_intent.id}")
        print(f"   Payment Intent status: {payment_intent.status}")
        
        # Confirm the payment intent (simulate payment)
        if payment_intent.status == 'requires_payment_method':
            print("\n3️⃣ Confirming payment intent...")
            # Update payment method if needed
            stripe.PaymentIntent.confirm(
                payment_intent.id,
                payment_method=payment_method.id if 'payment_method' in locals() else None,
            )
            print(f"✅ Payment intent confirmed")
            
            # Check updated status
            updated_pi = stripe.PaymentIntent.retrieve(payment_intent.id)
            print(f"   Updated status: {updated_pi.status}")
            
            if updated_pi.status == 'succeeded':
                print("✅ Payment succeeded!")
            else:
                print(f"⚠️  Payment status: {updated_pi.status}")
    
    # Wait a moment for Stripe to process
    print("\n4️⃣ Waiting for Stripe to process...")
    time.sleep(2)
    
    # Retrieve updated subscription
    updated_subscription = stripe.Subscription.retrieve(
        subscription.id,
        expand=['latest_invoice']
    )
    
    print(f"\n5️⃣ Updated subscription status: {updated_subscription.status}")
    
    if hasattr(updated_subscription, 'current_period_end'):
        period_end = datetime.fromtimestamp(updated_subscription.current_period_end)
        print(f"   Current period end: {period_end.isoformat()}")
    
    # Check invoice status
    if updated_subscription.latest_invoice:
        latest_invoice = updated_subscription.latest_invoice
        print(f"   Latest invoice status: {latest_invoice.status}")
        
        if latest_invoice.status == 'paid':
            print("✅ Invoice is paid!")
            
            print("\n6️⃣ Updating database...")
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
                        'subscription_id': updated_subscription.id,
                        'period_end': updated_subscription.current_period_end if hasattr(updated_subscription, 'current_period_end') else int(time.time()) + 30*24*60*60
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
            
        else:
            print(f"⚠️  Invoice not paid yet. Status: {latest_invoice.status}")
            print("\nTo complete manually in Stripe Dashboard:")
            print(f"1. Go to: https://dashboard.stripe.com/test/invoices/{latest_invoice.id}")
            print("2. Click 'Mark as paid'")
            print("3. Then run this script again or update database manually")
            
    else:
        print("⚠️  No invoice found for subscription")
        
except stripe.error.StripeError as e:
    print(f"❌ Stripe error: {e}")
    print("\nTry creating subscription through checkout instead:")
    print("1. Use the checkout URL from earlier")
    print("2. Complete payment in browser with test card")
    print("3. Webhook will update subscription automatically")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
