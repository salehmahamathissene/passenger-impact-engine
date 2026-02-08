import os
import sys
sys.path.append('src')

from dotenv import load_dotenv
load_dotenv('.env.working')

import stripe

print("🏦 REAL STRIPE INTEGRATION TEST")
print("=" * 50)

stripe_key = os.environ.get('STRIPE_SECRET_KEY')
stripe_price = os.environ.get('STRIPE_PRICE_PRO_MONTHLY')

print(f"Stripe Key: {stripe_key[:20]}...")
print(f"Price ID: {stripe_price}")

stripe.api_key = stripe_key

try:
    # 1. Test authentication
    print("\n1. 🔐 Testing authentication...")
    balance = stripe.Balance.retrieve()
    print(f"   ✅ Connected to Stripe Account")
    print(f"   Balance available: ${balance.available[0].amount/100:.2f} {balance.available[0].currency}")
    
    # 2. Test price retrieval
    print("\n2. 💰 Testing price retrieval...")
    price = stripe.Price.retrieve(stripe_price)
    print(f"   ✅ Price found: {price.id}")
    print(f"   Product: {price.product}")
    print(f"   Amount: ${price.unit_amount/100:.2f} {price.currency}")
    print(f"   Recurring: {price.recurring.interval if hasattr(price, 'recurring') else 'One-time'}")
    
    # 3. Test product retrieval
    print("\n3. 📦 Testing product retrieval...")
    product = stripe.Product.retrieve(price.product)
    print(f"   ✅ Product: {product.name}")
    print(f"   Description: {product.description[:50]}...")
    
    # 4. Create test customer
    print("\n4. 👤 Creating test customer...")
    customer = stripe.Customer.create(
        name="Test Enterprise Customer",
        email="enterprise-test@pie.example.com",
        metadata={
            "company_id": os.environ.get('COMPANY_ID', 'test'),
            "environment": "test"
        }
    )
    print(f"   ✅ Test customer created: {customer.id}")
    
    # 5. Create checkout session
    print("\n5. 🛒 Creating checkout session...")
    session = stripe.checkout.Session.create(
        customer=customer.id,
        line_items=[{
            "price": stripe_price,
            "quantity": 1
        }],
        mode="subscription",
        success_url="http://localhost:3000/billing/success",
        cancel_url="http://localhost:3000/billing/cancel",
        metadata={
            "company_id": os.environ.get('COMPANY_ID', 'test'),
            "test": "true"
        },
        subscription_data={
            "metadata": {
                "company_id": os.environ.get('COMPANY_ID', 'test'),
                "environment": "test"
            }
        }
    )
    print(f"   ✅ REAL CHECKOUT SESSION CREATED!")
    print(f"   Session ID: {session.id}")
    print(f"   URL: {session.url}")
    print(f"   Customer: {session.customer}")
    
    # Save session details
    import json
    session_data = {
        "session_id": session.id,
        "url": session.url,
        "customer_id": session.customer,
        "price_id": stripe_price,
        "created": session.created
    }
    
    with open('/tmp/stripe_checkout_session.json', 'w') as f:
        json.dump(session_data, f, indent=2)
    
    print(f"\n💾 Session saved to: /tmp/stripe_checkout_session.json")
    
    # 6. Clean up test data
    print("\n6. 🧹 Cleaning up test data...")
    try:
        # Delete test customer
        stripe.Customer.delete(customer.id)
        print(f"   ✅ Test customer deleted")
    except:
        print(f"   ⚠️  Could not delete test customer (may be in use)")
    
    print("\n" + "=" * 50)
    print("🎉 REAL STRIPE INTEGRATION: ✅ FULLY OPERATIONAL")
    print("=" * 50)
    print("\nReady for production billing!")
    
except stripe.error.AuthenticationError as e:
    print(f"❌ Stripe Authentication Error: {e}")
    print("\nPossible issues:")
    print("1. Check if Stripe account is active")
    print("2. Verify API key permissions")
    print("3. Ensure test mode is enabled")
    
except stripe.error.InvalidRequestError as e:
    print(f"❌ Invalid Request: {e}")
    print("\nCheck:")
    print(f"1. Price ID: {stripe_price}")
    print("2. Customer creation permissions")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
