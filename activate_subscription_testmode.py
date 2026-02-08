import os
import stripe
from datetime import datetime

stripe.api_key = os.environ["STRIPE_SECRET_KEY"]

customer_id = os.environ["STRIPE_CUSTOMER_ID"]  # set this
sub_id = os.environ["STRIPE_SUB_ID"]            # set this

# In test mode Stripe provides test PM ids like pm_card_visa
pm = stripe.PaymentMethod.retrieve("pm_card_visa")
stripe.PaymentMethod.attach(pm.id, customer=customer_id)

stripe.Customer.modify(
    customer_id,
    invoice_settings={"default_payment_method": pm.id},
)

# Now try to pay the latest invoice of the subscription
sub = stripe.Subscription.retrieve(sub_id, expand=["latest_invoice.payment_intent", "latest_invoice"])
inv = sub.latest_invoice
print("Subscription status:", sub.status)
print("Latest invoice:", inv.id, "status:", inv.status)

if inv.status != "paid":
    paid = stripe.Invoice.pay(inv.id)
    print("Invoice paid:", paid.status)

sub2 = stripe.Subscription.retrieve(sub_id)
print("✅ New subscription status:", sub2.status)

cpe = getattr(sub2, "current_period_end", None) or sub2.get("current_period_end")
print("current_period_end:", datetime.fromtimestamp(cpe).isoformat() if cpe else None)
