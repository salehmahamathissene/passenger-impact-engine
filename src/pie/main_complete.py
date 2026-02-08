"""
COMPLETE PASSENGER IMPACT ENGINE WITH BILLING
"""
from fastapi import FastAPI, HTTPException, Header, Depends, UploadFile, File, Form
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import uuid
import json
from datetime import datetime, date
from typing import Optional, List, Dict, Any

# Import billing module
try:
    from .stripe_integration import router as billing_router
    HAS_STRIPE = True
except ImportError:
    HAS_STRIPE = False

# ==================== CONFIGURATION ====================
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://pie:piepass@127.0.0.1:55432/pie_enterprise"
)
ENTERPRISE_ADMIN_KEY = os.getenv(
    "ENTERPRISE_ADMIN_KEY", 
    "test_admin_key_123"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# ==================== DEPENDENCIES ====================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_admin_key(x_admin_key: str = Header(None)):
    if not x_admin_key:
        raise HTTPException(status_code=401, detail="Admin key required")
    if x_admin_key != ENTERPRISE_ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return x_admin_key

# ==================== FASTAPI APP ====================
app = FastAPI(
    title="Passenger Impact Engine API",
    description="Enterprise platform for passenger impact analysis",
    version="5.0.0"
)

# Include billing routes if Stripe is available
if HAS_STRIPE:
    app.include_router(billing_router)

# ==================== COMPANY ENDPOINTS ====================
@app.post("/enterprise/companies", status_code=201)
async def create_company(
    legal_name: str = Form(...),
    tier: str = Form("mid"),
    industry: str = Form("airline"),
    country: str = Form("US"),
    trading_name: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    x_admin_key: str = Depends(verify_admin_key),
    db = Depends(get_db)
):
    """Create a new company"""
    try:
        # Check for duplicate
        check_sql = text("SELECT id FROM enterprise_companies WHERE legal_name = :name")
        existing = db.execute(check_sql, {"name": legal_name}).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Company already exists")
        
        # Create company
        company_id = str(uuid.uuid4())
        now = datetime.now()
        
        insert_sql = text("""
            INSERT INTO enterprise_companies (
                id, created_at, updated_at, legal_name, trading_name,
                tier, industry, country, phone, support_email, is_active, is_verified, total_spent
            ) VALUES (
                :id, :created_at, :updated_at, :legal_name, :trading_name,
                :tier, :industry, :country, :phone, :email, TRUE, FALSE, 0.00
            ) RETURNING id::text, legal_name, trading_name, tier, industry, country
        """)
        
        params = {
            "id": company_id,
            "created_at": now,
            "updated_at": now,
            "legal_name": legal_name,
            "trading_name": trading_name,
            "tier": tier,
            "industry": industry,
            "country": country,
            "phone": phone,
            "email": email
        }
        
        result = db.execute(insert_sql, params)
        db.commit()
        
        row = result.fetchone()
        
        # Create a free trial contract
        contract_id = str(uuid.uuid4())
        contract_sql = text("""
            INSERT INTO enterprise_contracts (
                id, company_id, contract_number, plan, signed_at, starts_at,
                status, monthly_fee_eur, created_at
            ) VALUES (
                :id, :company_id, :contract_number, 'trial', :signed_at, :starts_at,
                'active', 0, :created_at
            )
        """)
        
        db.execute(contract_sql, {
            "id": contract_id,
            "company_id": company_id,
            "contract_number": f"TRIAL-{datetime.now().strftime('%Y%m%d')}",
            "signed_at": now,
            "starts_at": now.date(),
            "created_at": now
        })
        db.commit()
        
        return {
            "message": "Company created with 30-day free trial",
            "id": row[0],
            "legal_name": row[1],
            "trading_name": row[2],
            "tier": row[3],
            "industry": row[4],
            "country": row[5],
            "trial_end": (now.date().replace(day=28) + datetime.timedelta(days=4)).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create company: {str(e)}")

# ... (rest of your existing endpoints)

@app.get("/")
async def root():
    """Root endpoint with business information"""
    return {
        "message": "Passenger Impact Engine API",
        "version": "5.0.0",
        "status": "operational",
        "pricing": {
            "starter": "$299/month",
            "pro": "$999/month",
            "enterprise": "$4,999/month"
        },
        "contact": "sales@passengerimpact.com"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
