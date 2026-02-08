from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional, Any

import stripe
from stripe._error import StripeError

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from pie.pro.enterprise_routes import require_company, get_db
from pie.pro.enterprise_models import EnterpriseCompany

router = APIRouter(prefix="/enterprise/billing", tags=["billing"])


class CheckoutReq(BaseModel):
    price_id: Optional[str] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


def _need_env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise HTTPException(status_code=500, detail=f"Missing env var: {name}")
    return v


def _set_stripe_key() -> None:
    stripe.api_key = _need_env("STRIPE_SECRET_KEY")


def _frontend_url(path: str) -> str:
    base = os.environ.get("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return base + path


def _stripe_503(e: Exception) -> HTTPException:
    msg = getattr(e, "user_message", None) or str(e)
    return HTTPException(status_code=503, detail=f"Stripe unavailable: {msg}")


def _unix_to_dt(ts: Optional[int]) -> Optional[datetime]:
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc)


@router.get("/ping")
def stripe_ping():
    _set_stripe_key()
    try:
        bal = stripe.Balance.retrieve()
        avail = bal.get("available", [])
        first = avail[0] if avail else {}
        amount = (first.get("amount", 0) or 0) / 100.0
        currency = first.get("currency", "unknown")
        return {"ok": True, "available": f"{amount:.2f} {currency}"}
    except StripeError as e:
        raise _stripe_503(e)
    except Exception as e:
        raise _stripe_503(e)


@router.get("/subscription")
def subscription_status(company: EnterpriseCompany = Depends(require_company)):
    plan = (getattr(company, "plan", None) or "free").lower()
    status = (getattr(company, "subscription_status", None) or "incomplete").lower()
    active = bool(getattr(company, "is_active", False)) and status in ("active", "trialing")
    return {
        "status": status,
        "plan": plan,
        "active": active,
        "stripe_customer_id": getattr(company, "stripe_customer_id", None),
        "stripe_subscription_id": getattr(company, "stripe_subscription_id", None),
        "current_period_end": (
            getattr(company, "current_period_end", None).isoformat()
            if getattr(company, "current_period_end", None)
            else None
        ),
    }


@router.post("/checkout")
def create_checkout(
    req: CheckoutReq,
    company: EnterpriseCompany = Depends(require_company),
    db: Session = Depends(get_db),
):
    _set_stripe_key()

    price_id = req.price_id or os.environ.get("STRIPE_PRICE_PRO_MONTHLY")
    if not price_id:
        raise HTTPException(status_code=500, detail="Missing price_id and STRIPE_PRICE_PRO_MONTHLY")

    success = req.success_url or _frontend_url("/billing/success")
    cancel = req.cancel_url or _frontend_url("/billing/cancel")

    try:
        customer_id = getattr(company, "stripe_customer_id", None)

        if not customer_id:
            cust = stripe.Customer.create(
                name=getattr(company, "legal_name", None) or getattr(company, "name", None) or "Company",
                metadata={"company_id": str(getattr(company, "id", ""))},
            )
            customer_id = cust["id"]

            if hasattr(company, "stripe_customer_id"):
                company.stripe_customer_id = customer_id
                db.add(company)
                db.commit()

        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success,
            cancel_url=cancel,
            allow_promotion_codes=True,
            metadata={"company_id": str(getattr(company, "id", ""))},
        )

        return {"url": session["url"], "customer_id": customer_id, "price_id": price_id}

    except StripeError as e:
        raise _stripe_503(e)
    except Exception as e:
        raise _stripe_503(e)


@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    _set_stripe_key()
    wh_secret = _need_env("STRIPE_WEBHOOK_SECRET")

    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload=payload, sig_header=sig, secret=wh_secret)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid webhook: {str(e)}")

    etype = event.get("type", "")
    obj = (event.get("data", {}) or {}).get("object", {}) or {}

    def set_company_status(company: EnterpriseCompany, sub: Any):
        company.plan = "pro"
        company.is_active = True
        company.subscription_status = (getattr(sub, "status", None) or sub.get("status") or "incomplete")
        company.stripe_subscription_id = getattr(sub, "id", None) or sub.get("id")
        cpe = getattr(sub, "current_period_end", None) or sub.get("current_period_end")
        company.current_period_end = _unix_to_dt(cpe)
        db.add(company)
        db.commit()

    def set_company_inactive(company: EnterpriseCompany, sub: Any):
        company.plan = "free"
        company.is_active = False
        company.subscription_status = (getattr(sub, "status", None) or sub.get("status") or "canceled")
        company.stripe_subscription_id = getattr(sub, "id", None) or sub.get("id")
        cpe = getattr(sub, "current_period_end", None) or sub.get("current_period_end")
        company.current_period_end = _unix_to_dt(cpe)
        db.add(company)
        db.commit()

    try:
        if etype == "checkout.session.completed":
            customer_id = obj.get("customer")
            company_id = (obj.get("metadata") or {}).get("company_id")

            if company_id:
                company = db.query(EnterpriseCompany).filter_by(id=company_id).first()
            else:
                company = db.query(EnterpriseCompany).filter_by(stripe_customer_id=customer_id).first()

            if company and customer_id and hasattr(company, "stripe_customer_id"):
                company.stripe_customer_id = customer_id
                db.add(company)
                db.commit()

        if etype in ("customer.subscription.created", "customer.subscription.updated"):
            customer_id = obj.get("customer")
            status = obj.get("status")
            company = db.query(EnterpriseCompany).filter_by(stripe_customer_id=customer_id).first()
            if company:
                if status in ("active", "trialing"):
                    set_company_status(company, obj)
                else:
                    set_company_inactive(company, obj)

        if etype == "customer.subscription.deleted":
            customer_id = obj.get("customer")
            company = db.query(EnterpriseCompany).filter_by(stripe_customer_id=customer_id).first()
            if company:
                set_company_inactive(company, obj)

        return {"received": True, "type": etype}

    except StripeError as e:
        raise _stripe_503(e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")
