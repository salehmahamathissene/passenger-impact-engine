from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException, Request, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
import stripe

from .config import settings
from .db import get_db
from .models import Company

router = APIRouter()
stripe.api_key = getattr(settings, "STRIPE_SECRET_KEY", "") or os.getenv("STRIPE_SECRET_KEY", "")


# ---------- Auth (simple API key for now) ----------
def require_api_key(x_api_key: str | None = Header(default=None)):
    required = os.getenv("API_KEY", "")
    if not required:
        # if you didn't set API_KEY, we don't block (for testing)
        return
    if not x_api_key or x_api_key != required:
        raise HTTPException(status_code=401, detail="Invalid API key")


def require_active_company(company_id: str, db: Session) -> Company:
    c = db.get(Company, company_id)
    if not c:
        raise HTTPException(status_code=404, detail="Company not found")
    if not c.is_active:
        raise HTTPException(status_code=402, detail="Subscription required")
    return c


# ---------- Schemas ----------
class CompanyCreate(BaseModel):
    company_id: str
    legal_name: str
    trading_name: str
    tier: str = "starter"
    industry: str = "airline"
    country: str = "US"


class CheckoutRequest(BaseModel):
    company_id: str
    tier: str = "starter"
    success_url: str
    cancel_url: str


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "passenger-impact-engine", "version": "2.1.0"}


@router.post("/companies")
async def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    existing = db.get(Company, company.company_id)
    if existing:
        return {"message": "Company already exists", "company_id": existing.company_id, "tier": existing.tier, "is_active": existing.is_active}

    c = Company(
        company_id=company.company_id,
        legal_name=company.legal_name,
        trading_name=company.trading_name,
        tier=company.tier,
        is_active=False,
    )
    db.add(c)
    db.commit()
    return {"message": "Company created", "company_id": c.company_id, "tier": c.tier, "is_active": c.is_active}


@router.post("/create-checkout-session")
async def create_checkout_session(request: CheckoutRequest, db: Session = Depends(get_db)):
    c = db.get(Company, request.company_id)
    if not c:
        raise HTTPException(status_code=404, detail="Create company first (/api/v1/companies)")

    # Pick price id from env
    tier = request.tier.lower()
    price_map = {
        "starter": os.getenv("STRIPE_STARTER_PRICE_ID", ""),
        "pro": os.getenv("STRIPE_PRO_PRICE_ID", ""),
        "enterprise": os.getenv("STRIPE_ENTERPRISE_PRICE_ID", ""),
    }
    price_id = price_map.get(tier, "")

    if not price_id:
        raise HTTPException(status_code=500, detail=f"Missing price id for tier={tier}. Set STRIPE_*_PRICE_ID env vars.")

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=request.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.cancel_url,
            metadata={"company_id": request.company_id, "tier": tier},
        )
        return {"checkout_url": session.url, "session_id": session.id, "tier": tier}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ Example paid endpoint (THIS is what makes money)
@router.post("/run-premium")
async def run_premium(payload: dict, company_id: str, db: Session = Depends(get_db), _=Depends(require_api_key)):
    c = require_active_company(company_id, db)
    # TODO: run your real premium simulation here
    return {"ok": True, "company_id": c.company_id, "tier": c.tier, "result": "premium simulation output"}


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # Must verify in real mode
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if not webhook_secret:
        raise HTTPException(status_code=500, detail="STRIPE_WEBHOOK_SECRET not set")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid signature: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")

    event_type = event["type"]
    obj = event["data"]["object"]

    # 1) checkout completed → activate
    if event_type == "checkout.session.completed":
        metadata = obj.get("metadata", {})
        company_id = metadata.get("company_id")
        tier = metadata.get("tier", "starter")

        customer_id = obj.get("customer")
        subscription_id = obj.get("subscription")

        if company_id:
            c = db.get(Company, company_id)
            if c:
                c.is_active = True
                c.tier = tier
                c.stripe_customer_id = customer_id
                c.stripe_subscription_id = subscription_id
                db.commit()

        return {"received": True, "event": event_type, "company_id": company_id, "tier": tier}

    # 2) invoice paid → keep active
    if event_type == "invoice.paid":
        subscription_id = obj.get("subscription")
        if subscription_id:
            c = db.query(Company).filter(Company.stripe_subscription_id == subscription_id).first()
            if c:
                c.is_active = True
                db.commit()
        return {"received": True, "event": event_type, "subscription_id": subscription_id}

    # 3) subscription canceled → deactivate
    if event_type in ("customer.subscription.deleted", "customer.subscription.updated"):
        sub_id = obj.get("id")
        status = obj.get("status", "")
        if sub_id:
            c = db.query(Company).filter(Company.stripe_subscription_id == sub_id).first()
            if c and status in ("canceled", "unpaid", "incomplete_expired"):
                c.is_active = False
                db.commit()
        return {"received": True, "event": event_type, "subscription_id": sub_id, "status": status}

    return {"received": True, "event": event_type}
