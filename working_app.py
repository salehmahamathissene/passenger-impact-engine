"""
Complete working Passenger Impact Engine
"""
from fastapi import FastAPI, HTTPException, Header, Depends
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import Optional, List
import uuid
from datetime import datetime
import json

# Configuration
DATABASE_URL = "postgresql://pie:piepass@127.0.0.1:55432/pie_enterprise"
ENTERPRISE_ADMIN_KEY = "test_admin_key_123"

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

app = FastAPI(
    title="Passenger Impact Engine",
    description="Enterprise-grade passenger impact analysis platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Dependency to get DB session
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

@app.get("/")
async def root():
    return {
        "message": "Passenger Impact Engine API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/enterprise/health")
async def enterprise_health(
    x_admin_key: str = Header(None),
    db = Depends(get_db)
):
    verify_admin_key(x_admin_key)
    
    try:
        result = db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "service": "enterprise",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/enterprise/companies")
async def list_companies(
    x_admin_key: str = Header(None),
    db = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    verify_admin_key(x_admin_key)
    
    try:
        # Get companies
        result = db.execute(
            text("""
                SELECT 
                    id::text, 
                    legal_name, 
                    trading_name, 
                    tier, 
                    industry, 
                    country, 
                    phone, 
                    support_email, 
                    billing_email, 
                    website,
                    employee_count, 
                    annual_revenue_eur, 
                    is_active, 
                    is_verified,
                    created_at
                FROM enterprise_companies 
                ORDER BY created_at DESC 
                LIMIT :limit OFFSET :skip
            """),
            {"limit": limit, "skip": skip}
        )
        
        companies = []
        for row in result:
            companies.append(dict(row._mapping))
        
        # Get total count
        count_result = db.execute(text("SELECT COUNT(*) FROM enterprise_companies"))
        total = count_result.scalar()
        
        return {
            "companies": companies,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/enterprise/companies")
async def create_company(
    company_data: dict,
    x_admin_key: str = Header(None),
    db = Depends(get_db)
):
    verify_admin_key(x_admin_key)
    
    try:
        # Prepare data
        company_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Extract fields with defaults
        legal_name = company_data.get("legal_name")
        if not legal_name:
            raise HTTPException(status_code=400, detail="legal_name is required")
        
        # Map tier to valid database value
        tier_map = {
            "small": "small",
            "medium": "medium", 
            "large": "large",
            "Small": "small",
            "Medium": "medium",
            "Large": "large",
            "S": "small",
            "M": "medium",
            "L": "large"
        }
        
        tier = company_data.get("tier", "small")
        tier = tier_map.get(tier, "small")  # Default to small if not mapped
        
        # Build SQL
        sql = """
            INSERT INTO enterprise_companies (
                id, created_at, updated_at,
                legal_name, trading_name, tier, industry, country,
                phone, support_email, billing_email, website,
                employee_count, annual_revenue_eur,
                is_active, is_verified, total_spent
            ) VALUES (
                :id, :created_at, :updated_at,
                :legal_name, :trading_name, :tier, :industry, :country,
                :phone, :support_email, :billing_email, :website,
                :employee_count, :annual_revenue_eur,
                TRUE, FALSE, 0.00
            )
            RETURNING id::text, legal_name, trading_name, tier, industry, country
        """
        
        params = {
            "id": company_id,
            "created_at": now,
            "updated_at": now,
            "legal_name": legal_name,
            "trading_name": company_data.get("trading_name"),
            "tier": tier,
            "industry": company_data.get("industry"),
            "country": company_data.get("country", "US"),
            "phone": company_data.get("phone"),
            "support_email": company_data.get("support_email"),
            "billing_email": company_data.get("billing_email"),
            "website": company_data.get("website"),
            "employee_count": company_data.get("employee_count"),
            "annual_revenue_eur": company_data.get("annual_revenue_eur")
        }
        
        # Execute
        result = db.execute(text(sql), params)
        db.commit()
        
        row = result.fetchone()
        
        if row:
            company = dict(row._mapping)
            return {
                "message": "Company created successfully",
                **company
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create company")
            
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create company: {str(e)}")

@app.get("/enterprise/companies/{company_id}")
async def get_company(
    company_id: str,
    x_admin_key: str = Header(None),
    db = Depends(get_db)
):
    verify_admin_key(x_admin_key)
    
    try:
        result = db.execute(
            text("""
                SELECT 
                    id::text, 
                    legal_name, 
                    trading_name, 
                    tier, 
                    industry, 
                    country, 
                    phone, 
                    support_email, 
                    billing_email, 
                    website,
                    employee_count, 
                    annual_revenue_eur, 
                    is_active, 
                    is_verified,
                    created_at
                FROM enterprise_companies 
                WHERE id = :company_id::uuid
            """),
            {"company_id": company_id}
        )
        
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Company not found")
        
        return dict(row._mapping)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
