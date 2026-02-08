"""
Super minimal working Passenger Impact Engine
"""
from fastapi import FastAPI, HTTPException, Header
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

# Configuration
DATABASE_URL = "postgresql://pie:piepass@127.0.0.1:55432/pie_enterprise"
ENTERPRISE_ADMIN_KEY = "test_admin_key_123"

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

app = FastAPI(
    title="Passenger Impact Engine (Minimal)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

def verify_admin_key(x_admin_key: str = Header(None)):
    if not x_admin_key:
        raise HTTPException(status_code=401, detail="Admin key required")
    if x_admin_key != ENTERPRISE_ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return x_admin_key

@app.get("/")
async def root():
    return {"message": "Passenger Impact Engine API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/enterprise/health")
async def enterprise_health(x_admin_key: str = Header(None)):
    verify_admin_key(x_admin_key)
    
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT 1"))
        db.close()
        return {
            "status": "healthy",
            "database": "connected",
            "service": "enterprise"
        }
    except Exception as e:
        db.close()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/enterprise/companies")
async def list_companies(
    skip: int = 0,
    limit: int = 100,
    x_admin_key: str = Header(None)
):
    verify_admin_key(x_admin_key)
    
    db = SessionLocal()
    try:
        # Get companies
        result = db.execute(
            text("""
                SELECT id, legal_name, trading_name, tier, industry, country, 
                       phone, support_email, billing_email, website,
                       employee_count, annual_revenue_eur, is_active, is_verified,
                       created_at
                FROM enterprise_companies 
                ORDER BY created_at DESC 
                LIMIT :limit OFFSET :skip
            """),
            {"limit": limit, "skip": skip}
        )
        
        companies = []
        for row in result:
            # Convert row to dict
            company = dict(row._mapping)
            # Convert UUID to string
            if 'id' in company:
                company['id'] = str(company['id'])
            companies.append(company)
        
        # Get total count
        count_result = db.execute(text("SELECT COUNT(*) FROM enterprise_companies"))
        total = count_result.scalar()
        
        db.close()
        
        return {
            "companies": companies,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        db.close()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/enterprise/companies")
async def create_company(
    company_data: dict,
    x_admin_key: str = Header(None)
):
    verify_admin_key(x_admin_key)
    
    db = SessionLocal()
    try:
        # Remove currency if present (not in table)
        if 'currency' in company_data:
            del company_data['currency']
        
        # Build SQL query
        columns = []
        values = []
        params = {}
        
        # Map of allowed columns (based on your table structure)
        allowed_columns = [
            'legal_name', 'trading_name', 'company_number', 'vat_number',
            'tier', 'industry', 'website', 'phone', 'support_email',
            'billing_email', 'country', 'employee_count', 'annual_revenue_eur'
        ]
        
        for key, value in company_data.items():
            if key in allowed_columns:
                columns.append(key)
                values.append(f":{key}")
                params[key] = value
        
        if not columns:
            raise HTTPException(status_code=400, detail="No valid company data provided")
        
        # Add required fields
        if 'legal_name' not in columns:
            raise HTTPException(status_code=400, detail="legal_name is required")
        
        # Add default values
        columns.append('is_active')
        values.append('TRUE')
        
        columns.append('is_verified')
        values.append('FALSE')
        
        sql = f"""
            INSERT INTO enterprise_companies ({', '.join(columns)})
            VALUES ({', '.join(values)})
            RETURNING id, legal_name, trading_name, tier, industry, country
        """
        
        result = db.execute(text(sql), params)
        db.commit()
        
        row = result.fetchone()
        
        if row:
            company = dict(row._mapping)
            company['id'] = str(company['id'])
            
            db.close()
            return {
                "message": "Company created successfully",
                **company
            }
        else:
            db.close()
            raise HTTPException(status_code=500, detail="Failed to create company")
            
    except Exception as e:
        db.rollback()
        db.close()
        raise HTTPException(status_code=500, detail=f"Failed to create company: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
