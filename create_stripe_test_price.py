import os
import stripe

# Your valid Stripe key
stripe.api_key = "sk_test_REDACTED"

print("💰 Creating Stripe test price...")
print("=" * 50)

try:
    # First, check existing products
    products = stripe.Product.list(limit=5)
    print(f"Found {len(products.data)} existing products:")
    for prod in products.data:
        print(f"  - {prod.name} ({prod.id})")
    
    # Check existing prices
    prices = stripe.Price.list(limit=5, active=True)
    print(f"\nFound {len(prices.data)} existing prices:")
    for price in prices.data:
        amount = price.unit_amount / 100 if price.unit_amount else 0
        print(f"  - ${amount:.2f} {price.currency} ({price.id})")
    
    print("\nDo you want to create a new test price?")
    print("1. Use existing price (copy ID above)")
    print("2. Create new test price")
    choice = input("Enter 1 or 2: ")
    
    if choice == "2":
        # Create new product
        product = stripe.Product.create(
            name="Passenger Impact Pro Monthly",
            description="Monthly subscription for Passenger Impact Pro"
        )
        print(f"\n✅ Created product: {product.id}")
        
        # Create price
        price = stripe.Price.create(
            product=product.id,
            unit_amount=9900,  # $99.00
            currency="usd",
            recurring={"interval": "month"}
        )
        print(f"✅ Created price: {price.id}")
        
        print(f"\n📋 Add this to your environment:")
        print(f"export STRIPE_PRICE_PRO_MONTHLY=\"{price.id}\"")
        
    else:
        if prices.data:
            print(f"\n📋 Suggested price ID: {prices.data[0].id}")
            print(f"Add to environment: export STRIPE_PRICE_PRO_MONTHLY=\"{prices.data[0].id}\"")
        else:
            print("\n❌ No existing prices found")
            
except stripe.error.AuthenticationError:
    print("❌ Invalid Stripe API key")
    print("Check your STRIPE_SECRET_KEY environment variable")
except Exception as e:
    print(f"❌ Error: {str(e)}")
