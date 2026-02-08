# Stripe Test Mode Guide

## Your Test Environment
- **Stripe Secret Key**: `sk_test_REDACTED`
- **Frontend URL**: `http://localhost:3000`
- **API URL**: `http://localhost:8080`

## Step 1: Create a Test Price
If you haven't created a price yet:

### Option A: Using Python (Run this):
```python
import stripe
stripe.api_key = "sk_test_REDACTED"

# Create product
product = stripe.Product.create(
    name="Passenger Impact Pro Monthly",
    description="Monthly subscription"
)

# Create price
price = stripe.Price.create(
    product=product.id,
    unit_amount=9900,  # $99.00
    currency="usd",
    recurring={"interval": "month"}
)

print(f"Price ID: {price.id}")  # Add this to .env.stripe
