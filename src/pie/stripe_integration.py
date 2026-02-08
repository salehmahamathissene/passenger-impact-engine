"""
Stripe integration for Passenger Impact Engine
"""
import stripe
import os
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Header, Depends, Request
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from typing import Optional

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pie:piepass@127.0.0.1:55432/pie_enterprise")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

router = APIRouter(prefix="/billing", tags=["billing"])

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_...")

# Product configuration - USING TEST MODE
PRICING_PLANS = {
    "starter": {
        "name": "Starter Plan",
        "price": 29900,  # $299 in cents
        "features": ["10,000 analyses/month", "Basic reporting", "Email support"],
        "stripe_price_id": os.getenv("STRIPE_STARTER_PRICE_ID", "price_1QjMNfBVxaxqk8ILH4ITpQtu"),  # Test price ID
        "limits": {
            "max_analyses": 10000,
            "max_companies": 1,
            "support_level": "email"
        }
    },
    "pro": {
        "name": "Pro Plan", 
        "price": 99900,  # $999 in cents
        "features": ["100,000 analyses/month", "Advanced reporting", "Phone support", "API access"],
        "stripe_price_id": os.getenv("STRIPE_PRO_PRICE_ID", "price_1QjMObBVxaxqk8IL4t77w7XW"),  # Test price ID
        "limits": {
            "max_analyses": 100000,
            "max_companies": 5,
            "support_level": "phone"
        }
    },
    "enterprise": {
        "name": "Enterprise Plan",
        "price": 499900,  # $4,999 in cents
        "features": ["Unlimited analyses", "Custom reporting", "24/7 support", "Dedicated account manager", "SLA guarantee"],
        "stripe_price_id": os.getenv("STRIPE_ENTERPRISE_PRICE_ID", "price_1QjMO3BVxaxqk8ILHp36mRrS"),  # Test price ID
        "limits": {
            "max_analyses": None,  # Unlimited
            "max_companies": 50,
            "support_level": "dedicated"
        }
    }
}

class CreateCheckoutSession(BaseModel):
    plan: str
    company_id: str
    success_url: str = "http://localhost:3000/success"
    cancel_url: str = "http://localhost:3000/cancel"

class CreateInvoiceRequest(BaseModel):
    company_id: str
    amount: float
    description: str = "Monthly subscription"
    currency: str = "usd"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/plans")
async def get_pricing_plans():
    """Get available pricing plans"""
    simplified_plans = {}
    for plan_id, details in PRICING_PLANS.items():
        simplified_plans[plan_id] = {
            "name": details["name"],
            "price": details["price"] / 100,  # Convert cents to dollars
            "features": details["features"],
            "stripe_price_id": details["stripe_price_id"]
        }
    return simplified_plans

@router.post("/create-checkout-session")
async def create_checkout_session(data: CreateCheckoutSession, db=Depends(get_db)):
    """Create a Stripe checkout session"""
    if data.plan not in PRICING_PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    if not data.company_id or data.company_id == "":
        raise HTTPException(status_code=400, detail="Company ID is required")
    
    try:
        # Verify company exists
        company = db.execute(
            text("SELECT id, legal_name FROM enterprise_companies WHERE id = :id"),
            {"id": data.company_id}
        ).fetchone()
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Create Stripe checkout session directly with price ID
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': PRICING_PLANS[data.plan]["stripe_price_id"],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=data.success_url,
            cancel_url=data.cancel_url,
            metadata={
                "company_id": data.company_id,
                "plan": data.plan
            },
            client_reference_id=data.company_id
        )
        
        # Create contract in database
        contract_id = str(uuid.uuid4())
        contract_number = f"CON-{datetime.now().strftime('%Y%m%d')}-{contract_id[:8].upper()}"
        
        db.execute(
            text("""
                INSERT INTO enterprise_contracts 
                (id, company_id, contract_number, plan, signed_at, status)
                VALUES (:id, :company_id, :contract_number, :plan, :signed_at, 'pending')
            """),
            {
                "id": contract_id,
                "company_id": data.company_id,
                "contract_number": contract_number,
                "plan": data.plan,
                "signed_at": datetime.now()
            }
        )
        db.commit()
        
        return {
            "checkout_url": session.url, 
            "session_id": session.id,
            "contract_id": contract_id,
            "message": "Checkout session created successfully"
        }
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request, db=Depends(get_db)):
    """Handle Stripe webhooks for subscription events"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle subscription events
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        company_id = session.metadata.get('company_id')
        plan = session.metadata.get('plan')
        
        if company_id:
            # Update contract status
            db.execute(
                text("""
                    UPDATE enterprise_contracts 
                    SET status = 'active', signed_at = NOW()
                    WHERE company_id = :company_id AND status = 'pending'
                    ORDER BY created_at DESC
                    LIMIT 1
                """),
                {"company_id": company_id}
            )
            db.commit()
        
    elif event['type'] == 'invoice.paid':
        invoice = event['data']['object']
        customer_id = invoice.customer
        
        # Record payment
        invoice_id = str(uuid.uuid4())
        invoice_number = f"PAID-INV-{datetime.now().strftime('%Y%m%d')}-{invoice_id[:8].upper()}"
        
        # In production, you'd look up company_id from Stripe customer metadata
        db.execute(
            text("""
                INSERT INTO enterprise_invoices 
                (id, company_id, invoice_number, amount_eur, currency, status, issued_at)
                VALUES (:id, :company_id, :invoice_number, :amount, :currency, 'paid', NOW())
            """),
            {
                "id": invoice_id,
                "company_id": customer_id,  # This would be looked up from your mapping
                "invoice_number": invoice_number,
                "amount": invoice.amount_paid / 100,  # Convert from cents
                "currency": invoice.currency.upper()
            }
        )
        db.commit()
    
    return {"status": "success", "event_type": event['type']}

@router.get("/demo-checkout")
async def demo_checkout():
    """Demo endpoint to show how checkout works (for testing)"""
    return {
        "instructions": "To test Stripe checkout:",
        "steps": [
            "1. Visit https://dashboard.stripe.com/test/products to create test products",
            "2. Get price IDs from Stripe dashboard",
            "3. Update STRIPE_*_PRICE_ID in your environment",
            "4. Use /create-checkout-session endpoint with a valid company_id",
            "5. Use test card: 4242 4242 4242 4242"
        ],
        "test_cards": {
            "success": "4242 4242 4242 4242",
            "requires_auth": "4000 0025 0000 3155",
            "declined": "4000 0000 0000 0002"
        }
    }
