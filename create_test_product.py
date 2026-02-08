import os
import stripe

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

try:
    # Create a test product
    product = stripe.Product.create(
        name="Passenger Impact Pro Monthly",
        description="Monthly subscription for Passenger Impact Pro plan"
    )
    print(f"✅ Created product: {product.id}")
    
    # Create a price for the product
    price = stripe.Price.create(
        product=product.id,
        unit_amount=9900,  # $99.00
        currency="usd",
        recurring={"interval": "month"}
    )
    print(f"✅ Created price: {price.id}")
    print(f"📋 Add this to your .env.stripe file:")
    print(f"   export STRIPE_PRICE_PRO_MONTHLY=\"{price.id}\"")
    
except Exception as e:
    print(f"❌ Failed to create product/price: {str(e)}")
    print("\n📝 You can also create manually in Stripe Dashboard:")
    print("1. Go to https://dashboard.stripe.com/test/products")
    print("2. Click 'Add Product'")
    print("3. Name: 'Passenger Impact Pro Monthly'")
    print("4. Add price: $99/month")
    print("5. Copy the Price ID (looks like price_1Qb...)")
