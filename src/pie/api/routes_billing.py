from __future__ import annotations

import os
import stripe
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from pie.db import get_db
from pie.models import Company, Subscription

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

class CheckoutReq(BaseModel):
    company_id: str
    price_id: str
    success_url: str
    cancel_url: str

@router.post("/billing/checkout-session")
def create_checkout_session(req: CheckoutReq, db: Session = Depends(get_db)):
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="STRIPE_SECRET_KEY missing")

    company = db.get(Company, req.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="company not found")

    # Create Stripe customer if needed
    sub = db.query(Subscription).filter(Subscription.company_id == company.id).first()
    if not sub:
        sub = Subscription(company_id=company.id, tier="pro", status="inactive")
        db.add(sub)
        db.commit()

    if not sub.stripe_customer_id:
        customer = stripe.Customer.create(name=company.name, metadata={"company_id": company.id})
        sub.stripe_customer_id = customer["id"]
        db.commit()

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=sub.stripe_customer_id,
        line_items=[{"price": req.price_id, "quantity": 1}],
        success_url=req.success_url,
        cancel_url=req.cancel_url,
        metadata={"company_id": company.id},
    )
    return {"checkout_url": session["url"], "session_id": session["id"]}

class PortalReq(BaseModel):
    company_id: str
    return_url: str

@router.post("/billing/portal")
def billing_portal(req: PortalReq, db: Session = Depends(get_db)):
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="STRIPE_SECRET_KEY missing")

    sub = db.query(Subscription).filter(Subscription.company_id == req.company_id).first()
    if not sub or not sub.stripe_customer_id:
        raise HTTPException(status_code=404, detail="no stripe customer")

    portal = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=req.return_url,
    )
    return {"url": portal["url"]}
