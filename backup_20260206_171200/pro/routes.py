from __future__ import annotations

import stripe
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from .settings import settings
from .db import get_db
from .models import Order, OrderStatus, Job
from .queue import enqueue_order_job


router = APIRouter(prefix="/pro", tags=["pro"])

# Check if we have real Stripe keys
def is_real_stripe_key(key: str) -> bool:
    """Check if this is a real Stripe key (not test mode placeholder)"""
    if not key:
        return False
    if key.startswith("sk_test_") and len(key) > 30:  # Real keys are longer
        # Check it's not our placeholder
        if "TEST_MODE" in key or "REPLACE" in key or "PASTE" in key:
            return False
        return True
    return False


# Only set Stripe API key if it's a real key
if is_real_stripe_key(settings.STRIPE_SECRET_KEY):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe_enabled = True
    print("✅ Stripe enabled with real API key")
else:
    stripe_enabled = False
    print("⚠️  Stripe not configured. Running in TEST MODE.")
    print("   To enable real payments, add real Stripe keys to .env file")


class CheckoutRequest(BaseModel):
    email: EmailStr
    plan: str  # "starter" | "pro" | "enterprise"


def price_for(plan: str) -> int:
    p = plan.lower()
    if p == "starter":
        return settings.STARTER_PRICE_EUR
    if p == "pro":
        return settings.PRO_PRICE_EUR
    if p == "enterprise":
        return settings.ENTERPRISE_PRICE_EUR
    raise ValueError(f"Invalid plan: {plan}")


@router.post("/checkout")
async def create_checkout(request: CheckoutRequest, db: Session = Depends(get_db)):
    """Create checkout session for a plan"""
    
    # Validate plan
    try:
        amount_cents = price_for(request.plan)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Create order
    order = Order(
        customer_email=request.email,
        plan=request.plan,
        amount_cents=amount_cents,
        currency=settings.CURRENCY,
        status=OrderStatus.pending
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # If we have REAL Stripe keys, create real checkout
    if stripe_enabled:
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": settings.CURRENCY,
                            "product_data": {
                                "name": f"PIE {request.plan.title()} Plan",
                                "description": f"Passenger Impact Engine {request.plan.title()} Analysis"
                            },
                            "unit_amount": amount_cents,
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=settings.STRIPE_SUCCESS_URL.replace("{ORDER_ID}", str(order.id)),
                cancel_url=settings.STRIPE_CANCEL_URL.replace("{ORDER_ID}", str(order.id)),
                customer_email=request.email,
                metadata={"order_id": str(order.id)}
            )
            
            # Update order with Stripe session
            order.stripe_checkout_session_id = checkout_session.id
            db.commit()
            
            return {
                "checkout_url": checkout_session.url, 
                "order_id": order.id,
                "payment_mode": "stripe_live",
                "message": "Real Stripe checkout created"
            }
            
        except stripe.error.StripeError as e:
            # If Stripe fails, fall back to test mode
            print(f"Stripe error, falling back to test mode: {e}")
            return {
                "message": "Stripe error, using test mode",
                "order_id": order.id,
                "test_payment_url": f"/pro/test-pay/{order.id}",
                "payment_mode": "test_fallback",
                "error": str(e)
            }
    else:
        # No real Stripe keys - test mode
        return {
            "message": "Running in test mode. No real payment required.",
            "order_id": order.id,
            "test_payment_url": f"/pro/test-pay/{order.id}",
            "payment_mode": "test",
            "instructions": "Use the test-pay endpoint to simulate payment."
        }


@router.post("/test-pay/{order_id}")
async def test_payment(order_id: int, db: Session = Depends(get_db)):
    """TEST ONLY: Mark order as paid (for development without Stripe)"""
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = OrderStatus.paid
    db.commit()
    
    # Queue background job
    enqueue_order_job(order.id)
    
    return {
        "message": "Order marked as paid (test mode)",
        "order_id": order_id,
        "job_queued": True,
        "note": "This is for development. Use real Stripe keys for production payments."
    }


@router.get("/orders/{order_id}")
async def get_order(order_id: int, db: Session = Depends(get_db)):
    """Get order status"""
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    job_data = None
    if order.job:
        job_data = {
            "status": order.job.status,
            "artifact_path": order.job.artifact_path,
            "error": order.job.error,
            "processing_time_ms": order.job.processing_time_ms,
            "runs_completed": order.job.runs_completed
        }
    
    return {
        "id": order.id,
        "email": order.customer_email,
        "plan": order.plan,
        "amount_cents": order.amount_cents,
        "currency": order.currency,
        "status": order.status,
        "created_at": order.created_at.isoformat(),
        "stripe_checkout_session_id": order.stripe_checkout_session_id,
        "stripe_payment_intent_id": order.stripe_payment_intent_id,
        "notes": order.notes,
        "job": job_data
    }


@router.get("/orders")
async def list_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all orders"""
    orders = db.query(Order).order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for order in orders:
        result.append({
            "id": order.id,
            "email": order.customer_email,
            "plan": order.plan,
            "amount_cents": order.amount_cents,
            "status": order.status,
            "created_at": order.created_at.isoformat(),
            "has_job": order.job is not None
        })
    
    return result


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "pro",
        "stripe_enabled": stripe_enabled,
        "mode": "production" if stripe_enabled else "test",
        "instructions": "Add real Stripe keys to .env for production payments" if not stripe_enabled else None
    }
