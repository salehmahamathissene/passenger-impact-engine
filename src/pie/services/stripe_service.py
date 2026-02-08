import stripe
from pie.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_checkout_session(customer_email: str, tenant_id: int):
    return stripe.checkout.Session.create(
        mode="subscription",
        customer_email=customer_email,
        line_items=[{"price": settings.STRIPE_PRICE_BASIC, "quantity": 1}],
        success_url=f"{settings.BASE_URL}/billing/success?tenant_id={tenant_id}",
        cancel_url=f"{settings.BASE_URL}/billing/cancel",
        metadata={"tenant_id": str(tenant_id)},
    )
