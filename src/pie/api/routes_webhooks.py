from __future__ import annotations

import os
import stripe
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.orm import Session

from pie.db import SessionLocal
from pie.models import Company, Subscription

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    if not WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="STRIPE_WEBHOOK_SECRET missing")

    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {e}")

    # use DB session manually (webhooks are outside Depends)
    db: Session = SessionLocal()
    try:
        etype = event["type"]
        data = event["data"]["object"]

        # subscription status changed
        if etype in ("customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"):
            customer_id = data.get("customer")
            sub_id = data.get("id")
            status = data.get("status", "inactive")

            sub = db.query(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()
            if sub:
                sub.stripe_subscription_id = sub_id
                sub.status = status

                # simple rule: active/trialing -> pro tier
                if status in ("active", "trialing"):
                    sub.tier = "pro"
                    company = db.get(Company, sub.company_id)
                    if company:
                        company.tier = "pro"
                else:
                    # downgrade (you can keep grace logic later)
                    company = db.get(Company, sub.company_id)
                    if company:
                        company.tier = "free"
                db.commit()

        return {"received": True}
    finally:
        db.close()
