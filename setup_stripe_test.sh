#!/bin/bash
echo "💳 SETTING UP STRIPE FOR TESTING"
echo "================================"

# Create test products in Stripe (run this after getting your Stripe API key)
cat > create_stripe_products.py << 'PYEOF'
import stripe
import os

# Get your test key from https://dashboard.stripe.com/test/apikeys
stripe.api_key = "sk_test_REDACTED..."  # Replace with your test key

products = {
    "starter": {
        "name": "Starter Plan",
        "description": "10,000 analyses/month, Basic reporting, Email support",
        "price": 29900  # $299 in cents
    },
    "pro": {
        "name": "Pro Plan",
        "description": "100,000 analyses/month, Advanced reporting, Phone support, API access",
        "price": 99900  # $999 in cents
    },
    "enterprise": {
        "name": "Enterprise Plan",
        "description": "Unlimited analyses, Custom reporting, 24/7 support, Dedicated account manager, SLA guarantee",
        "price": 499900  # $4,999 in cents
    }
}

print("Creating Stripe products...")
print("=" * 50)

for plan, details in products.items():
    # Create product
    product = stripe.Product.create(
        name=details["name"],
        description=details["description"]
    )
    
    # Create price
    price = stripe.Price.create(
        product=product.id,
        unit_amount=details["price"],
        currency="usd",
        recurring={"interval": "month"}
    )
    
    print(f"{plan.upper()} PLAN:")
    print(f"  Product ID: {product.id}")
    print(f"  Price ID: {price.id}")
    print(f"  Amount: ${details['price']/100}/month")
    print(f"  Export command:")
    print(f"  export STRIPE_{plan.upper()}_PRICE_ID='{price.id}'")
    print("-" * 50)

print("\n✅ Products created!")
print("\n📋 Add these to your environment:")
print("export STRIPE_SECRET_KEY='sk_test_...'")
print("export STRIPE_WEBHOOK_SECRET='whsec_...'")
print("# Add the price IDs from above")
PYEOF

echo "Instructions:"
echo "1. Get your Stripe test key from: https://dashboard.stripe.com/test/apikeys"
echo "2. Update the stripe.api_key in create_stripe_products.py"
echo "3. Run: python create_stripe_products.py"
echo "4. Copy the price IDs and add them to your .env file"
echo
echo "For quick testing, you can use these test price IDs:"
echo "Starter: price_1QjMNfBVxaxqk8ILH4ITpQtu"
echo "Pro: price_1QjMObBVxaxqk8IL4t77w7XW"
echo "Enterprise: price_1QjMO3BVxaxqk8ILHp36mRrS"
