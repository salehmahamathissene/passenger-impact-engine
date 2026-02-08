from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import desc

import stripe

from .settings import settings
from .db import get_db
from .models import Order, OrderStatus
from .queue import enqueue_order_job

router = APIRouter(prefix="/pro", tags=["pro"])


def stripe_enabled() -> bool:
    k = (settings.STRIPE_SECRET_KEY or "").strip()
    return k.startswith("sk_live_") or k.startswith("sk_test_")


class CheckoutRequest(BaseModel):
    email: EmailStr
    plan: str  # starter|pro|enterprise


def price_for(plan: str) -> int:
    p = plan.lower()
    if p == "starter":
        return settings.STARTER_PRICE_EUR
    if p == "pro":
        return settings.PRO_PRICE_EUR
    if p == "enterprise":
        return settings.ENTERPRISE_PRICE_EUR
    raise HTTPException(status_code=400, detail="Invalid plan")


@router.get("/health")
def pro_health():
    return {"status": "healthy", "service": "pro", "stripe_enabled": stripe_enabled()}


@router.post("/checkout")
def checkout(req: CheckoutRequest, db: Session = Depends(get_db)):
    # STRICT: If Stripe not configured, do NOT create orders. No toy/test mode.
    if not stripe_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured. Set real STRIPE_SECRET_KEY/WEBHOOK secret for payments.",
        )

    stripe.api_key = settings.STRIPE_SECRET_KEY.strip()

    amount = price_for(req.plan)
    currency = settings.CURRENCY

    # Create order pending until webhook marks paid
    order = Order(
        customer_email=req.email,
        plan=req.plan.lower(),
        amount_cents=amount,
        currency=currency,
        status=OrderStatus.pending,
        notes="Stripe Checkout created",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            customer_email=req.email,
            line_items=[
                {
                    "price_data": {
                        "currency": currency,
                        "product_data": {"name": f"Passenger Impact Engine - {req.plan.upper()}"},
                        "unit_amount": amount,
                    },
                    "quantity": 1,
                }
            ],
            success_url=settings.STRIPE_SUCCESS_URL.replace("{ORDER_ID}", str(order.id)),
            cancel_url=settings.STRIPE_CANCEL_URL.replace("{ORDER_ID}", str(order.id)),
            metadata={"order_id": str(order.id), "plan": req.plan.lower()},
        )
        order.stripe_checkout_session_id = session.id
        db.commit()
        return {"checkout_url": session.url, "order_id": order.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")


@router.get("/orders")
def list_orders(limit: int = 50, db: Session = Depends(get_db)):
    q = db.query(Order).order_by(desc(Order.created_at)).limit(limit).all()
    return [
        {
            "id": o.id,
            "email": o.customer_email,
            "plan": o.plan,
            "amount_cents": o.amount_cents,
            "status": o.status.value,
            "created_at": o.created_at.isoformat(),
            "has_job": o.job is not None,
        }
        for o in q
    ]


@router.get("/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    o = db.get(Order, order_id)
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "id": o.id,
        "email": o.customer_email,
        "plan": o.plan,
        "amount_cents": o.amount_cents,
        "currency": o.currency,
        "status": o.status.value,
        "created_at": o.created_at.isoformat(),
        "stripe_checkout_session_id": o.stripe_checkout_session_id,
        "stripe_payment_intent_id": o.stripe_payment_intent_id,
        "notes": o.notes,
        "job": None if not o.job else {
            "status": o.job.status.value,
            "artifact_path": o.job.artifact_path,
            "error": o.job.error,
            "processing_time_ms": o.job.processing_time_ms,
            "runs_completed": o.job.runs_completed,
        }
    }
