from __future__ import annotations

import os
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

# TODO: import your auth + db deps
# from pie.pro.enterprise_auth import require_company
# from pie.db import get_db
# from pie.pro.models import EnterpriseInvoice

router = APIRouter(prefix="/enterprise/billing", tags=["enterprise-billing"])

stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:8080")


class CheckoutRequest(BaseModel):
    invoice_id: str  # your internal invoice UUID as string


@router.post("/checkout-session")
def create_checkout_session(req: CheckoutRequest):  # add company/db deps in your project
    # 1) Load invoice from DB and validate belongs to company and unpaid
    # inv = db.get(EnterpriseInvoice, uuid.UUID(req.invoice_id))
    # if not inv or inv.company_id != company.id: raise 404
    # if inv.status == "paid": raise 400

    # 2) Choose Stripe Price (monthly plan)
    # Create these prices in Stripe dashboard and store IDs in env
    price_id = os.getenv("STRIPE_PRICE_PRO_MONTHLY")
    if not price_id:
        raise HTTPException(500, "STRIPE_PRICE_PRO_MONTHLY not configured")

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{APP_BASE_URL}/enterprise/billing/success?invoice_id={req.invoice_id}",
        cancel_url=f"{APP_BASE_URL}/enterprise/billing/cancel?invoice_id={req.invoice_id}",
        metadata={
            "invoice_id": req.invoice_id,
        },
    )

    return {"url": session.url, "id": session.id}
@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    whsec = os.environ["STRIPE_WEBHOOK_SECRET"]

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, whsec)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {e}")

    etype = event["type"]
    data = event["data"]["object"]

    # ✅ We mark paid only on invoice.payment_succeeded (best) OR checkout.session.completed (ok)
    if etype == "checkout.session.completed":
        # subscription checkout finished — payment may not be final for some payment methods
        # OK to store stripe ids here, but don't mark paid yet if you want strictness.
        invoice_id = data["metadata"].get("invoice_id")
        # TODO: store stripe_session_id, stripe_customer_id, stripe_subscription_id on your invoice/company

    if etype == "invoice.payment_succeeded":
        # This is STRIPE invoice for the subscription payment
        # We need metadata: easiest way is to attach metadata to subscription OR customer
        # If you only have metadata on checkout.session, then store mapping in DB at checkout.session.completed time.
        pass

    return {"ok": True}
