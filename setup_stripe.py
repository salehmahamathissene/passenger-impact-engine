import stripe
stripe.api_key = "sk_test_..."

# Create products
products = {
    "starter": {"name": "Starter Plan", "price": 29900},
    "pro": {"name": "Pro Plan", "price": 99900},
    "enterprise": {"name": "Enterprise Plan", "price": 499900}
}

for plan, details in products.items():
    product = stripe.Product.create(name=details["name"])
    price = stripe.Price.create(
        product=product.id,
        unit_amount=details["price"],
        currency="usd",
        recurring={"interval": "month"}
    )
    print(f"{plan}: {product.id} - ${details['price']/100}/month")
