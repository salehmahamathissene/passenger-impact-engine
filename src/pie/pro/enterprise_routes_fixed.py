"""
Fixed enterprise routes for Passenger Impact Engine
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from .db import get_db
from .settings import get_settings

# Import models
try:
    from .enterprise_models import EnterpriseCompany, EnterpriseContact, EnterpriseContract, EnterpriseInvoice
    MODELS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: Could not import enterprise models: {e}")
    MODELS_AVAILABLE = False
    # Create dummy classes
    class EnterpriseCompany:
        pass
    class EnterpriseContact:
        pass
    class EnterpriseContract:
        pass
    class EnterpriseInvoice:
        pass

router = APIRouter()
settings = get_settings()

def verify_admin_key(x_admin_key: str = Header(None)):
    """Verify admin key for enterprise endpoints"""
    if not x_admin_key:
        raise HTTPException(status_code=401, detail="Admin key required")
    if x_admin_key != settings.ENTERPRISE_ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return x_admin_key

@router.get("/health")
async def health(db: Session = Depends(get_db), admin_key: str = Depends(verify_admin_key)):
    """Health check endpoint"""
    try:
        # Test database connection with text() wrapper
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "service": "enterprise",
            "admin_key_valid": True,
            "models_available": MODELS_AVAILABLE
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/companies")
async def list_companies(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_key: str = Depends(verify_admin_key)
):
    """List all companies"""
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Enterprise models not available")
    
    companies = db.query(EnterpriseCompany).offset(skip).limit(limit).all()
    
    # Convert to dict to avoid serialization issues
    companies_data = []
    for company in companies:
        company_dict = {}
        # Use actual fields from the model
        for attr in ['id', 'legal_name', 'trading_name', 'tier', 'industry', 'country', 
                     'phone', 'support_email', 'billing_email', 'website', 'employee_count',
                     'annual_revenue_eur', 'is_active', 'is_verified']:
            if hasattr(company, attr):
                value = getattr(company, attr)
                # Handle special types
                if attr == 'id':
                    value = str(value)
                company_dict[attr] = value
        companies_data.append(company_dict)
    
    return {
        "companies": companies_data,
        "total": len(companies_data),
        "skip": skip,
        "limit": limit
    }

@router.post("/companies")
async def create_company(
    company_data: dict,
    db: Session = Depends(get_db),
    admin_key: str = Depends(verify_admin_key)
):
    """Create a new company"""
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Enterprise models not available")
    
    try:
        # Remove 'currency' field if present (model doesn't have it)
        if 'currency' in company_data:
            del company_data['currency']
        
        # Map incoming data to actual model fields
        field_mapping = {
            "legal_name": "legal_name",
            "trading_name": "trading_name", 
            "tier": "tier",
            "industry": "industry",
            "country": "country",
            "phone": "phone",
            "support_email": "support_email",
            "billing_email": "billing_email",
            "website": "website",
            "employee_count": "employee_count",
            "annual_revenue_eur": "annual_revenue_eur",
            "company_number": "company_number",
            "vat_number": "vat_number"
        }
        
        company_kwargs = {}
        for json_field, model_field in field_mapping.items():
            if json_field in company_data:
                company_kwargs[model_field] = company_data[json_field]
        
        # Set defaults
        if "is_active" not in company_kwargs:
            company_kwargs["is_active"] = True
        if "is_verified" not in company_kwargs:
            company_kwargs["is_verified"] = False
        
        # Create company with actual model fields
        company = EnterpriseCompany(**company_kwargs)
        
        db.add(company)
        db.commit()
        db.refresh(company)
        
        # Return success response
        return {
            "message": "Company created successfully",
            "id": str(company.id),
            "legal_name": company.legal_name,
            "trading_name": company.trading_name,
            "tier": company.tier,
            "industry": company.industry,
            "country": company.country
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create company: {str(e)}")

@router.get("/companies/{company_id}")
async def get_company(
    company_id: str,
    db: Session = Depends(get_db),
    admin_key: str = Depends(verify_admin_key)
):
    """Get company by ID"""
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=500, detail="Enterprise models not available")
    
    company = db.query(EnterpriseCompany).filter(EnterpriseCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Convert to dict
    company_dict = {}
    for attr in ['id', 'legal_name', 'trading_name', 'tier', 'industry', 'country', 
                 'phone', 'support_email', 'billing_email', 'website', 'employee_count',
                 'annual_revenue_eur', 'is_active', 'is_verified']:
        if hasattr(company, attr):
            value = getattr(company, attr)
            if attr == 'id':
                value = str(value)
            company_dict[attr] = value
    
    return company_dict

@router.get("/test/model-info")
async def model_info(admin_key: str = Depends(verify_admin_key)):
    """Get information about the EnterpriseCompany model"""
    if not MODELS_AVAILABLE:
        return {"error": "Models not available"}
    
    try:
        # Check what columns the table has
        if hasattr(EnterpriseCompany, '__table__'):
            columns = {col.name: str(col.type) for col in EnterpriseCompany.__table__.columns}
        else:
            columns = {}
        
        return {
            "model": "EnterpriseCompany",
            "columns": columns,
            "models_available": MODELS_AVAILABLE
        }
    except Exception as e:
        return {"error": str(e)}
